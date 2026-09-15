# YouTube采集平台

> **平台类型**：视频平台
> **状态**：已接入（复用multiplatform-media-fetch技能）
> **依赖**：`/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py`

---

## 功能

- **视频下载**：支持YouTube视频链接
- **播放列表下载**：支持整个播放列表
- **音频提取**：只下载音频（用于转写）
- **字幕下载**：自动下载字幕（优先官方字幕，支持多语言）
- **多音轨**：支持指定音轨语言
- **清晰度选择**：best/360/480/720/1080/1440/2160

---

## 使用方法

### 1. 下载单个视频

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  -o library/01_video/youtube/
```

### 2. 下载播放列表

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx" \
  --playlist \
  -o library/01_video/youtube/
```

### 3. 只下载音频（用于转写）

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --audio --audio-format mp3 \
  -o library/02_audio/youtube/
```

### 4. 下载字幕

```bash
# 自动下载字幕（优先官方字幕）
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --subs \
  -o library/01_video/youtube/
```

### 5. 指定音轨语言

```bash
# 英语音轨
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --audio-lang en \
  -o library/01_video/youtube/
```

### 6. 使用代理（需要VPN时）

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --proxy http://127.0.0.1:7890 \
  -o library/01_video/youtube/
```

---

## 注意事项

1. **代理**：YouTube需要VPN代理，使用`--proxy http://127.0.0.1:7890`（ClashX默认端口）
2. **字幕优先**：有字幕时优先下载字幕，不需要转写
3. **多音轨**：YouTube部分视频有多语言音轨，用`--audio-lang`指定
4. **输出目录**：视频存`library/01_video/youtube/`，音频存`library/02_audio/youtube/`

---

## 待接入

- [ ] YouTube频道视频列表采集（需要YouTube API或浏览器自动化）
- [ ] PlatformFetcher接口实现（继承platforms/base.py）
- [ ] 批量采集编排（参考B站batch_build.py）

---

## 参考

- 技能路径：`/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/`
- 下载脚本：`scripts/media_downloader.py`
- 批量脚本：`scripts/batch_fetch.py`
- 转写脚本：`scripts/transcribe.py`（FunASR本地离线）
