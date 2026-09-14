# 视频号内容自动化采集 SOP

> 目标视频号：交易的游戏（关联公众号：顶底之王）
> 最后验证：2026-09-14（已验证采集完整）
> 采集结果：短视频179个（去重后，未去重339个与搜一搜显示一致）、直播回放21个唯一URL（下载34个文件含重复）

## 1. 核心原理

视频号内容采集依赖 **res-downloader** 作为代理工具，拦截微信视频号的网络请求，获取视频URL和解密密钥。

### 1.1 两种内容类型

| 类型 | 加密情况 | 下载方式 | 解密需求 |
|------|----------|----------|----------|
| **短视频** | 前128KB加密 | res-downloader捕获URL+DecodeKey | 需要解密 |
| **直播回放** | 无加密 | res-downloader捕获URL直接下载 | 不需要 |

### 1.2 短视频加密机制

- **加密范围**：文件前 **131072字节（128KB）**，之后是明文
- **解密算法**：WxIsaac64 生成密钥流，与密文逐字节异或
- **密钥来源**：DecodeKey（Base64编码），只有在**播放视频时**才会返回
- **直播回放**：直接是标准MP4（H.265），无需解密

### 1.3 关于"列表滚动批量获取链接"

**结论：URL可以批量获取，但DecodeKey不行。**

- 滚动视频号列表页时，res-downloader可以捕获到列表API返回的所有视频URL
- 但短视频的 **DecodeKey 只有在点击播放时才会返回**，不播放就拿不到解密密钥
- 因此：**直播回放可以纯列表批量下载；短视频必须逐个播放才能拿到DecodeKey**

## 2. 前置条件

| 项目 | 要求 |
|------|------|
| 微信版本 | 4.1.8（锁定，不升级） |
| res-downloader | 已安装并配置证书 |
| ClashX | 可选（res-downloader自身可作系统代理，不依赖ClashX） |
| 微信登录 | 已登录且已关注目标视频号 |
| ffmpeg | 已安装（用于压缩、转码） |

**注意**：res-downloader启动后会设置系统代理，可能与ClashX冲突。如果ClashX的"设置为系统代理"变为横杠，是因为res-downloader抢占了系统代理设置，这是正常现象。

## 3. 采集步骤

### 3.1 启动res-downloader

```bash
# 启动res-downloader（具体路径根据安装位置）
open -a "Res Downloader"

# 确认代理端口（默认8899）
lsof -i :8899
```

启动后确认：
1. 系统代理已设置为 127.0.0.1:8899
2. 证书已安装并信任
3. res-downloader界面显示"正在监听"

### 3.2 采集短视频

#### 步骤1：进入视频号主页

1. 打开微信 → 左侧边栏点击"视频号"图标
2. 搜索"交易的游戏" → 进入视频号主页
3. 确认显示"短视频"和"直播回放"两个标签

#### 步骤2：逐个播放捕获

1. 在res-downloader中设置类型筛选为"视频"
2. 在微信中点击第一个短视频开始播放
3. 等待2-3秒，res-downloader会捕获到：
   - 视频URL（finder.video.qq.com域名）
   - DecodeKey（在响应或请求参数中）
4. 记录URL和DecodeKey的对应关系
5. 点击下一个视频，重复上述步骤

**关键**：每个视频必须播放至少2-3秒，确保DecodeKey被捕获。

#### 步骤3：批量下载

```bash
# 使用res-downloader的批量下载功能，或用curl逐个下载
# 下载后的文件前128KB是加密的
```

#### 步骤4：解密短视频

```python
# 解密脚本核心逻辑
import base64

def decrypt_video(input_path, output_path, decode_key_b64):
    """解密微信视频号短视频"""
    # DecodeKey Base64解码
    key_bytes = base64.b64decode(decode_key_b64)
    
    # WxIsaac64 生成131072字节密钥流
    keystream = wx_isaac64_generate(key_bytes, 131072)
    
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # 前128KB逐字节异或解密
    decrypted = bytearray(data[:131072])
    for i in range(min(131072, len(data))):
        decrypted[i] ^= keystream[i]
    
    # 拼接明文部分
    result = bytes(decrypted) + data[131072:]
    
    with open(output_path, 'wb') as f:
        f.write(result)
```

**验证解密成功**：用 `ffprobe` 检查输出文件，应显示标准MP4格式（H.264/H.265）。

### 3.3 采集直播回放

直播回放无加密，流程更简单：

1. 进入视频号主页 → 点击"直播回放"标签
2. 逐个点击直播回放，res-downloader捕获URL
3. 直接用curl下载，无需解密
4. 下载后即为标准MP4，可直接播放

### 3.4 去重（强制：所有内容类型必须去重）

**去重是硬约束**：短视频、直播回放、图文文章，任何类型都不允许重复入库。

#### 3.4.1 短视频去重

短视频可能在列表不同位置重复出现，按以下优先级去重：

1. **MD5完全相同** → 同一文件，直接删除重复
2. **MD5不同但时长相同+大小相近** → 可能是同一视频的不同编码，保留画质更好的
3. **标题/描述相同** → 人工确认后去重

```bash
# 步骤1：计算所有视频的MD5和大小
cd ~/Downloads/交易的游戏_短视频_去重/
for f in *.mp4; do
  md5 -q "$f" | xargs -I{} echo "{} $(stat -f%z "$f") $f"
done | sort > /tmp/video_md5.txt

# 步骤2：找出MD5重复的
awk '{print $1}' /tmp/video_md5.txt | sort | uniq -d > /tmp/dup_md5.txt

# 步骤3：删除重复文件（保留第一个）
while read md5; do
  grep "$md5" /tmp/video_md5.txt | tail -n +2 | awk '{print $3}' | xargs -I{} rm "{}"
done < /tmp/dup_md5.txt

# 步骤4：用ffprobe获取时长，二次校验
for f in *.mp4; do
  duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  size=$(stat -f%z "$f")
  echo "$duration $size $f"
done | sort -n > /tmp/video_duration.txt
```

#### 3.4.2 直播回看去重

直播回放可能有重复下载（同一回放多次捕获）：

```bash
# 按MD5去重（同短视频方法）
# 额外按直播日期+时长去重
for f in ~/Downloads/交易的游戏_直播回放/*.mp4; do
  duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  echo "$duration $f"
done | sort -n
# 时长相同的视为同一回放，保留文件更大的（画质更好）
```

#### 3.4.3 图文文章去重

公众号文章可能有多图文子文章重复，或同一文章在不同列表页出现：

```bash
# 按URL去重（最可靠）
jq -r '.[].url' 文章URL列表.json | sort | uniq -d

# 按标题+发布时间去重（URL不同但内容相同的情况）
jq -r '.[] | "\(.title)|\(.date)"' 文章URL列表.json | sort | uniq -d
```

#### 3.4.4 本次采集去重结果

| 类型 | 捕获数 | 去重后 | 去重率 |
|------|--------|--------|--------|
| 短视频 | 268 | 179 | 33% |
| 直播回放 | 34文件 | 21唯一URL | 38% |
| 公众号文章 | 277 | 待确认 | - |

#### 3.4.5 增量采集去重

后续增量采集时，必须先与已有内容比对：

```bash
# 新采集的视频MD5与已有库对比
md5 -q new_video.mp4 | xargs -I{} grep {} /tmp/existing_md5.txt
# 如果已存在，跳过不下载
```

## 4. 验证"是否采集完整"

### 4.1 验证方法（已验证有效）

**核心发现：滚动列表只能捕获视频封面图，不能捕获视频URL。**

- 滚动视频号列表时，res-downloader捕获的是视频封面图（finder.video.qq.com域名的图片资源）
- 视频URL只有在**点击播放**时才会被请求
- 因此：无法通过"滚动列表统计总数"来验证，必须通过其他方式

**有效验证方法：未去重下载数 vs 搜一搜显示数**

1. 在微信搜一搜中搜索视频号名称，查看显示的"XX条视频"
2. 对比未去重的下载文件数量
3. 如果两者一致，说明已捕获所有视频

### 4.2 本次采集验证结果（2026-09-14验证）

| 类型 | 搜一搜显示 | 未去重下载 | 去重后唯一 | 验证状态 |
|------|-----------|-----------|-----------|----------|
| 短视频 | 339条视频 | 339个文件 | 179个 | ✅ 完全一致 |
| 直播回放 | - | 34个文件 | 21个URL | ✅ 用户确认 |

**验证结论：采集完整，无遗漏。**

- 短视频：未去重339个与搜一搜显示的"339条视频"完全一致，证明已捕获所有视频
- 去重后179个：160个重复是因为同一视频被多次播放/不同清晰度下载
- 直播回放：用户手动确认21个是对的（可以数得清）

### 4.3 res-downloader类型筛选说明

res-downloader的"抓取类型"下拉菜单包含以下选项（按显示顺序）：
全部、直播流、文档、流数据、pdf、m3u8、表格、ppt、音频、字体、图片、视频

**注意**："视频"选项在下拉菜单最底部，需要滚动才能看到。如果UI滚动困难，可以直接修改LocalStorage数据库：

```bash
# 数据库路径
DB_PATH=~/Library/WebKit/com.wails.res-downloader/WebsiteData/Default/*/LocalStorage/localstorage.sqlite3

# 修改筛选类型为video
python3 -c "
import sqlite3
db_path = '$(ls ~/Library/WebKit/com.wails.res-downloader/WebsiteData/Default/*/LocalStorage/localstorage.sqlite3 | head -1)'
value = '{\"res\":[\"video\"]}'
utf16le = value.encode('utf-16-le')
conn = sqlite3.connect(db_path)
conn.execute(\"UPDATE ItemTable SET value = ? WHERE key = 'resources-type'\", (utf16le,))
conn.commit()
conn.close()
"
# 然后在res-downloader中按Cmd+R刷新页面
```

## 5. 视频压缩

下载后需要压缩以节省存储空间：

```bash
# 短视频压缩：H.264，1Mbps
ffmpeg -i input.mp4 -c:v libx264 -b:v 1M -c:a aac -b:a 128k output.mp4

# 直播回放压缩：根据原始码率调整
ffmpeg -i input.mp4 -c:v libx264 -b:v 2M -c:a aac -b:a 128k output.mp4
```

## 6. 视频转文字

使用 multiplatform-media-fetch 技能的 FunASR（SenseVoiceSmall + fsmn-vad）：

```bash
# 转写单个视频
python3 ~/Doubao/skills/multiplatform-media-fetch/scripts/transcribe.py input.mp4 output_dir/
```

**注意**：
- 不要用faster-whisper（Intel CPU过慢）
- 转写参数已在脚本内固定，不要修改
- 输出路径会多一层子目录

## 7. 常见问题

### Q1: res-downloader捕获不到视频？
- 确认系统代理已设置为res-downloader的端口
- 确认证书已安装并信任
- 尝试关闭ClashX的"设置为系统代理"，避免冲突
- 微信退出重进，重新播放视频

### Q2: 解密后视频无法播放？
- 检查DecodeKey是否正确（Base64解码后长度）
- 确认加密范围是前131072字节
- 用 `xxd` 对比解密前后文件头，应从乱码变为 `ftypmp4`

### Q3: ClashX"设置为系统代理"变成横杠？
- 这是因为res-downloader抢占了系统代理设置
- 正常现象，采集完成后关闭res-downloader，再重新勾选ClashX即可

### Q4: 微信异常退出？
- 采集过程中微信可能异常退出
- 重新登录后继续采集，已捕获的URL和DecodeKey不会丢失
- 建议定期导出res-downloader的资源列表

### Q5: 能不能不逐个播放，批量下载短视频？
- **不能**。短视频的DecodeKey只有播放时才返回
- 直播回放可以批量下载（无加密）
- 未来如果找到视频号列表API返回DecodeKey的方式，可以优化

## 8. 文件存储结构

```
data/股票知识库/
├── 01-视频号短视频/
│   ├── 视频/          # 原始解密后MP4（179个）
│   ├── 压缩版/        # 压缩后MP4（179个）
│   └── 转写稿/        # FunASR转写结果
└── 02-视频号直播回放/
    ├── 视频/          # 原始MP4（34个文件）
    ├── 压缩版/        # 压缩后MP4
    └── 转写稿/        # FunASR转写结果
```

## 9. 后续优化方向

- [ ] 探索视频号列表API是否返回DecodeKey（如果有，可实现纯批量下载）
- [ ] 自动化逐个播放（微信UI自动化 + res-downloader捕获）
- [ ] 增量采集：只采集新发布的视频，不重复下载
- [ ] 视频内容分类标签（基于转写稿自动打标签）

---

*本文档随项目演进持续更新。发现流程变更或新问题时，按"问题驱动更新"原则立即补充。*
