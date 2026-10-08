# B站采集平台

> **平台类型**：视频平台
> **状态**：已接入列表采集（待接入下载+转写编排）
> **来源**：迁移自珠宝知识库项目（gemology-kb），已适配为可配置

---

## 功能

- **视频列表采集**：获取UP主的全部投稿视频列表
- **合集/系列采集**：获取UP主的合集和系列列表
- **双通道**：
  - **wbi签名通道**（首选）：设备指纹 + wbi key签名，翻页获取
  - **dynamic动态流通道**（备用）：免登录、不易被封，offset递归
- **防风控**：随机间隔、慢速翻页、断点续拉
- **可配置**：UID通过命令行参数或环境变量指定

---

## 脚本

| 脚本 | 用途 |
|------|------|
| `bili_list.py` | UP主投稿/合集列表采集（核心脚本） |

---

## 使用方法

### 1. 采集视频列表（最小验证）

```bash
# 验证一页（推荐先跑这个确认网络和签名正常）
python3 platforms/bilibili/bili_list.py wbi --uid 1841256325 --max-pages 1
```

### 2. 采集全量视频+合集

```bash
# 拉全量投稿+合集（慢速，防风控）
python3 platforms/bilibili/bili_list.py wbi --uid 1841256325
```

### 3. 动态流通道（备用）

```bash
# wbi通道被风控时使用动态流通道
python3 platforms/bilibili/bili_list.py dynamic --uid 1841256325
```

### 4. 环境变量配置

```bash
export BILI_UID="1841256325"           # 默认UP主UID
export BILI_OUTPUT_DIR="library/00_manifest/bilibili"  # 输出目录
```

---

## 输出

输出到 `library/00_manifest/bilibili/`：

| 文件 | 内容 |
|------|------|
| `up_{UID}_videos.json` | 投稿视频列表（bvid、标题、发布时间、时长、播放量、URL） |
| `up_{UID}_seasons.json` | 合集/系列列表（ID、类型、名称、总数、描述） |
| `up_{UID}_videos_dynamic.json` | 动态流通道的视频列表（备用） |
| `up_{UID}_dyn_checkpoint.json` | 动态流断点续拉进度 |

---

## 技术原理

### wbi签名通道

1. **设备指纹**：调用 `x/frontend/finger/spi` 获取 buvid3/buvid4
2. **wbi key**：调用 `x/web-interface/nav` 获取 img_url/sub_url，拼接后经MIXIN_TAB混淆得到32位mixin key
3. **签名**：请求参数 + wts时间戳 → URL编码排序 → MD5(mixin) → w_rid
4. **翻页**：`x/space/wbi/arc/search` (ps=50, pn递增)

### dynamic动态流通道

1. **免登录**：不需要cookie，直接调用动态流API
2. **offset递归**：每次返回next_offset，作为下一次请求的offset
3. **断点续拉**：进度保存到checkpoint文件，中断后可续拉
4. **有界重试**：同一游标最多重试3次，应对瞬时软限流

---

## 待接入

- [ ] 视频下载编排（参考珠宝项目batch_build.py，需抽象行业分类规则）
- [ ] 视频转写编排（参考珠宝项目batch_transcribe.py）
- [ ] 合集详情采集（collect_seasons.py，需Chrome登录态）
- [ ] PlatformFetcher接口实现（继承platforms/base.py）

---

## 参考

- B站API文档：https://github.com/SocialSisterYi/bilibili-API-collect
