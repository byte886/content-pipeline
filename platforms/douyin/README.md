# 抖音采集平台

> **平台类型**：短视频平台
> **状态**：已接入（复用multiplatform-media-fetch技能）
> **依赖**：`/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py`

---

## 功能

- **视频下载**：支持抖音视频链接或纯数字ID
- **音频提取**：只下载音频（用于转写）
- **字幕下载**：自动下载字幕（如有）
- **防风控**：默认复用Chrome Cookie，限速下载
- **清晰度选择**：best/360/480/720/1080

---

## 使用方法

### 1. 下载单个视频

```bash
# 通过视频链接下载
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.douyin.com/video/7295678901234567890" \
  -o library/01_video/douyin/

# 通过纯数字ID下载
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "7295678901234567890" \
  -o library/01_video/douyin/
```

### 2. 只下载音频（用于转写）

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.douyin.com/video/7295678901234567890" \
  --audio --audio-format mp3 \
  -o library/02_audio/douyin/
```

### 3. 下载最小音频（转写够用，省流量）

```bash
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/media_downloader.py \
  "https://www.douyin.com/video/7295678901234567890" \
  --smallest --audio \
  -o library/02_audio/douyin/
```

### 4. 批量下载

```bash
# 批量下载脚本（技能自带）
python3 /Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/batch_fetch.py \
  --input video_list.txt \
  -o library/01_video/douyin/
```

---

## 注意事项

1. **Cookie复用**：抖音默认复用Chrome Cookie，需要Chrome已登录抖音网页版
2. **防风控**：脚本内置限速和请求间隔，不要多线程并发
3. **代理**：抖音国内直连即可，不需要代理
4. **输出目录**：视频存`library/01_video/douyin/`，音频存`library/02_audio/douyin/`

---

## 待接入

- [ ] 抖音UP主主页视频列表采集（需要逆向或浏览器自动化）
- [ ] PlatformFetcher接口实现（继承platforms/base.py）
- [ ] 批量采集编排（参考B站batch_build.py）

---

## 参考

- 技能路径：`/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/`
- 下载脚本：`scripts/media_downloader.py`
- 批量脚本：`scripts/batch_fetch.py`
