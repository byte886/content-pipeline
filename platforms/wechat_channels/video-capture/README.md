# 视频号捕获工具（命令行版）

基于 res-downloader 核心逻辑改造的无UI命令行工具，用于自动捕获微信视频号的视频URL。

## 功能特性

- ✅ 自动捕获视频号短视频和直播回放URL
- ✅ 自动保存到JSON文件（支持断点续传、去重）
- ✅ 可选自动下载视频
- ✅ 无需UI操作，纯命令行运行
- ✅ 自动生成CA证书

## 编译

```bash
cd tools/video-capture
go build -o video-capture .
```

## 使用方法

### 1. 首次使用：信任CA证书

首次运行会自动生成 `ca.crt` 和 `ca.key`，需要在系统中信任证书：

```bash
# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca.crt
```

或手动：双击 `ca.crt` → 钥匙串访问 → 双击证书 → 信任 → 始终信任。

### 2. 启动捕获工具

```bash
# 基本用法（只捕获URL，不下载）
./video-capture

# 指定输出文件
./video-capture -output videos.json

# 自动下载视频
./video-capture -download -download-dir ./downloads

# 指定端口
./video-capture -port 8899
```

### 3. 设置系统代理

macOS：
- 系统设置 → 网络 → 高级 → 代理
- 勾选"网页代理(HTTP)"和"安全网页代理(HTTPS)"
- 服务器：127.0.0.1，端口：8899

或命令行：
```bash
# 设置代理
networksetup -setwebproxy "Wi-Fi" 127.0.0.1 8899
networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 8899

# 关闭代理
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off
```

### 4. 在微信中浏览视频号

打开微信 → 视频号 → 进入目标账号 → 浏览视频列表，工具会自动捕获所有视频URL。

### 5. 停止

按 `Ctrl+C` 停止，捕获的URL会自动保存。

## 输出格式

`videos.json` 格式：
```json
[
  {
    "id": "abc123...",
    "url": "https://finder.video.qq.com/...",
    "cover_url": "https://...",
    "size": 10485760,
    "description": "视频标题/描述",
    "classify": "video",
    "suffix": ".mp4",
    "decode_key": "",
    "other_data": {
      "wx_file_formats": "format1#format2#format3"
    },
    "captured_at": "2026-09-14 21:00:00"
  }
]
```

## 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-port` | 8899 | 代理服务器端口 |
| `-output` | videos.json | 视频URL输出文件 |
| `-download` | false | 是否自动下载视频 |
| `-download-dir` | ./downloads | 视频下载目录 |
| `-ca-cert` | 空 | CA证书路径（留空自动生成） |
| `-ca-key` | 空 | CA私钥路径（留空自动生成） |

## 工作原理

1. 启动本地HTTPS代理服务器（MITM中间人攻击）
2. 当访问视频号页面时，注入JavaScript代码
3. Hook视频对象的 `get media()` 方法
4. 视频加载时自动把视频信息发送到代理
5. 解析并保存视频URL

## 与原版 res-downloader 的区别

| 功能 | 原版 | 本工具 |
|------|------|--------|
| UI界面 | ✅ Wails桌面应用 | ❌ 纯命令行 |
| 代理捕获 | ✅ | ✅ |
| JS注入 | ✅ | ✅ |
| 自动保存URL | ❌ 需手动导出 | ✅ 自动保存 |
| 自动下载 | ❌ 需手动点击 | ✅ 可选 |
| 去重 | ✅ | ✅ |
| 多平台支持 | ✅ | ✅ |

## 注意事项

1. **证书信任**：必须信任CA证书，否则HTTPS无法解密
2. **系统代理**：需要设置系统代理指向本工具
3. **微信版本**：建议使用微信4.x版本
4. **视频URL有效期**：视频号URL有token，会过期，捕获后尽快下载
5. **风控**：频繁操作可能触发微信风控，建议合理使用

## 故障排查

### 无法捕获视频
1. 确认CA证书已信任
2. 确认系统代理已设置
3. 确认微信走的是系统代理
4. 尝试刷新视频号页面

### HTTPS报错
- 重新生成CA证书：删除 ca.crt 和 ca.key 后重启
- 重新信任证书

### 端口被占用
```bash
# 查看端口占用
lsof -i :8899
# 更换端口
./video-capture -port 9000
```
