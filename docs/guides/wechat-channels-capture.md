# 视频号内容采集SOP

> **文档类型**：场景SOP
> **前置依赖**：[wechat-basic-operations.md](wechat-basic-operations.md)，必读：§0工具选型、§1操作前准备、§2主窗口搜索流程、§3浏览器窗口通用规则；常见问题遇到再查

---

## 快速参考
| 任务 | 命令 |
|------|------|
| 启动捕获（直连，推荐） | `cd platforms/wechat_channels/video-capture && ./video-capture -port 8899 -output /tmp/capture.json -upstream ""` |
| 启动捕获（带ClashX上游） | `./video-capture -port 8899 -output /tmp/capture.json -upstream http://127.0.0.1:7890` |
| 停止捕获 | `bash platforms/wechat_channels/video-capture/stop.sh`（禁止kill -9，否则系统代理不会自动清除） |
| 批量下载短视频 | `python3 platforms/wechat_channels/video-downloader/batch_download_v4.py videos_short.json <outdir> short` |
| 批量下载直播回放 | `python3 platforms/wechat_channels/video-downloader/batch_download_v4.py videos_live.json <outdir> live` |

---

## 1. UI操作流程（视频号特有）
通用激活、搜索、窗口操作全部走基础SOP，视频号特有步骤：
1.  主窗口搜索目标视频号名称，在搜一搜结果页确认条目下方有"视频号"灰色标签，点击进入视频号主页
2.  进入视频号主页后，及时关掉多余的搜一搜标签页，只保留视频号当前页面
3.  标签切换优先用JS注入直接点击DOM元素，绕开鼠标坐标点不准的问题
4.  先切换到「视频」标签，鼠标放在列表区域内，滚动列表直到完全加载到底
5.  再切换到「直播回放」标签，同样滚动列表直到完全加载到底
> 滚动时鼠标必须放在列表内容区域内，落在空白区域滚动无效。

---

## 2. URL捕获流程
1.  UI操作开始前启动捕获工具，工具启动时自动设置系统代理，退出时自动清除；自动检查ClashX(7890)是否可用，不可用则降级直连，国内视频号直连即可
2.  按§1完成UI滚动加载，所有视频URL会被捕获到`/tmp/capture.json`
3.  滚动完成后执行stop.sh停止捕获，自动恢复系统代理
4.  从捕获结果提取URL，按`encfilekey`全局去重，按文件大小分类：<100MB为短视频，≥100MB为直播回放

> 代理仅在捕获URL的几分钟内设置，下载阶段不走代理；Chrome等读系统代理的GUI程序会短暂受影响，iTerm/TUN模式不受影响。

---

## 3. 下载与解密
1.  短视频：批量下载脚本自动完成解密，解密原理为用捕获到的`DecodeKey`（9-10位数字）通过ISAAC64生成128KB字节数组，与文件前128KB做XOR
2.  直播回放：无需解密，直接下载
3.  有效性验证：下载完成后检查文件头为`ftyp`即为有效MP4
4.  视频质量：默认URL为低分辨率（约2-5MB/个），高质量URL在参数后加`&X-snsvideoflag=xWT111`，文件体积约大70%

---

## 4. 视频号特有问题
| 问题 | 解决 |
|---|---|
| 微信不走代理 | video-capture自动对所有活动网络服务设置代理，无需手动 |
| 短视频无法播放 | 短视频需要解密，批量下载脚本自动处理 |
| DecodeKey获取位置 | 捕获数据中的`decode_key`字段 |
| 直播回放是否需要解密 | 不需要 |
| 下载的视频只有2-5MB | 默认低分辨率，按§3高质量URL参数获取 |

---

## 5. 参考
- 微信基础操作：[wechat-basic-operations.md](wechat-basic-operations.md)
- 公众号采集：[wechat-official-article.md](wechat-official-article.md)
- 视频质量URL详细研究：`RESEARCH-video-quality-url.md`
- 解密源码：`platforms/wechat_channels/video-downloader/wechat_decrypt.js`
