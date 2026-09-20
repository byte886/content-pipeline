# 视频号内容采集SOP

> **文档类型**：SOP
> **更新时间**：2026-09-18
> **前置依赖**：[SOP-wechat-basic-operations.md](SOP-wechat-basic-operations.md)（窗口管理、搜索、鼠标控制）

---

## 快速参考

| 任务 | 命令 |
|------|------|
| 启动捕获（直连） | `cd platforms/wechat_channels/video-capture && ./video-capture -port 8899 -output /tmp/capture.json -upstream ""` |
| 启动捕获（带ClashX上游） | `./video-capture -port 8899 -output /tmp/capture.json -upstream http://127.0.0.1:7890` |
| 停止捕获 | Ctrl+C（自动清除代理），或 `bash stop.sh` |
| 批量下载+解密 | `python3 platforms/wechat_channels/video-downloader/batch_download_v4.py <list.json> <outdir> <live\|short>` |
| 手动解密 | `node platforms/wechat_channels/video-downloader/wechat_decrypt.js <DecodeKey> <file.mp4>` |

---

## 1. 采集流程

### 1.1 启动捕获工具

```bash
cd platforms/wechat_channels/video-capture
# 直连模式（国内视频号足够，推荐）
nohup ./video-capture -port 8899 -output /tmp/capture.json -upstream "" > /tmp/video_capture_stdout.log 2>&1 &
echo $! > /tmp/video_capture_pid.txt
```

工具启动时自动设置系统代理，退出时自动清除。启动时自动检查ClashX(7890)是否可用，不可用则降级直连。

### 1.2 在微信中操作

按 [wechat-basic-operations SOP](wechat-basic-operations.md) 完成：
1. 激活主窗口，Cmd+F 搜索视频号名称
2. 在搜索结果中点击视频号条目（悬停确认灰色后点击）
3. 进入视频号主页后，及时关掉多余的搜一搜标签页，只保留视频号当前页面
4. 切换到「视频」标签，滚动列表到底部
5. 切换到「直播回放」标签，滚动列表到底部

> 滚动时鼠标必须放在列表区域内，否则滚动无效。

### 1.3 停止捕获

```bash
bash platforms/wechat_channels/video-capture/stop.sh
# 或 kill $(cat /tmp/video_capture_pid.txt)
```

> ⚠️ 禁止用kill -9，否则系统代理不会自动清除。

### 1.4 导出与去重

从 `/tmp/capture.json` 提取视频，按 `encfilekey` 去重，按大小分类（<100MB短视频，>=100MB直播回放）。

### 1.5 下载与解密

```bash
# 短视频（自动解密）
python3 platforms/wechat_channels/video-downloader/batch_download_v4.py videos_short.json output_dir short

# 直播回放（无需解密）
python3 platforms/wechat_channels/video-downloader/batch_download_v4.py videos_live.json output_dir live
```

验证：文件头为 `ftyp` 即为有效MP4。

---

## 2. 技术要点

### 2.1 代理说明

微信不走Wi-Fi代理，必须对**所有活动网络服务**设置代理。video-capture自动处理此问题。

**代理影响范围**：仅捕获URL阶段（几分钟）设置系统代理，下载阶段不走代理。Chrome等读系统代理的GUI程序会受影响，iTerm/TUN模式不受影响。

### 2.2 视频解密

短视频加密：用 `DecodeKey`（9-10位数字）通过ISAAC64生成128KB字节数组，与文件前128KB做XOR。直播回放无需解密。

> 详细原理见源码 `platforms/wechat_channels/video-downloader/wechat_decrypt.js`。

### 2.3 视频质量

- 默认URL：xWT113格式，约2.32MB/个
- 高质量：URL后加 `&X-snsvideoflag=xWT111`，约3.92MB/个（大69%）
- 详细研究：[RESEARCH-video-quality-url.md](RESEARCH-video-quality-url.md)

---

## 3. 常见问题

| 问题 | 解决方案 |
|------|---------|
| 微信不走代理 | video-capture自动对所有活动网络服务设置代理，无需手动 |
| 视频无法播放 | 短视频需解密，batch_download_v4.py自动处理 |
| DecodeKey在哪 | 捕获数据中字段 `decode_key` |
| 直播回放要解密吗 | 不需要 |
| 视频只有2-5MB | 默认低分辨率，见§2.3 |
| 设置全局代理影响其他程序 | 仅捕获阶段几分钟，工具退出自动清除代理 |

---

## 4. 参考文档

- 微信基本操作：[wechat-basic-operations.md](wechat-basic-operations.md)
- 公众号采集：[wechat-official-article.md](wechat-official-article.md)
- 视频质量研究：[RESEARCH-video-quality-url.md](RESEARCH-video-quality-url.md)
