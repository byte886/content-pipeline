# 视频号内容采集SOP

> **文档类型**：场景SOP
> **前置依赖**：[wechat-basic-operations.md](wechat-basic-operations.md)，必读：§0工具选型、§1操作前准备、§2主窗口搜索流程、§3浏览器窗口通用规则；常见问题遇到再查

---

## 快速参考
| 任务 | 命令 |
|------|------|
| 启动捕获（直连，推荐） | `cd platforms/wechat_channels/video-capture && ./video-capture -port 8899 -output /tmp/capture.json -upstream ""` |
| 启动捕获（带ClashX上游） | `./video-capture -port 8899 -output /tmp/capture.json -upstream http://127.0.0.1:7890` |
| 启动捕获（换签直链+decode_key，短视频解密必需） | `./video-capture -short-probe -output capture_shortprobe.json -upstream http://127.0.0.1:7890`（须在 Cmd+Q 重启微信**之前**启动） |
| **全自动抓全量（推荐，自动滚动+自动切tab）** | `./video-capture -short-probe -autoscroll -output capture_full.json -upstream http://127.0.0.1:7890`，启动后只需**刷新一次视频号主页**，见 §2.1 |
| 合并多次捕获并对账 | 见 §2.2（输出为多段 JSON 拼接，需 raw_decode 展平；按 encfilekey 去重、md5 对账） |
| 停止捕获 | `bash platforms/wechat_channels/video-capture/stop.sh`（禁止kill -9，否则系统代理不会自动清除） |
| 批量下载短视频 | `python3 platforms/wechat_channels/video-downloader/batch_download_v4.py <capture.json> <outdir> short [start] [min\|default\|max]`，知识型默认 `min` |
| 批量下载直播回放 | `python3 platforms/wechat_channels/video-downloader/batch_download_v4.py <capture.json> <outdir> live [start] [min\|default\|max]` |

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

### 2.1 全自动列表抓取（`-autoscroll`，✅ 2026-09-21 验证）

启动带 `-short-probe -autoscroll` 的捕获后，**人工只需刷新一次视频号主页**，注入 JS 自动完成两个标签的全量翻页，无需手动滚动、无需手动切 tab：

1. 「视频」tab：每 800ms 把列表容器直接跳到底（`scrollTop=scrollHeight` + wheel + window.scrollBy 三管齐下）触发懒加载下一页；连续 8 次（约 6.4s）高度不增且仍在底部判“无更多”，回顶再扫一遍补漏。
2. 视频翻完后，自动对 `.tab` 中文本为「直播回放」的元素派发完整 `pointerover/move/down→mousedown→pointerup/mouseup→click` 事件（标签 DOM 实测为 `<div class="tab">视频</div>` / `<div class="tab tab--active">…</div>`），冷却 4 拍等面板加载。
3. 容器切换靠“元素引用 + 可见性滞回”检测（旧容器从可见列表消失＝真正切了 tab），随后对回放列表重复快速翻页；两 tab 都翻完自动停止。

关键工程点（曾踩坑，勿回退）：
- **容器标识绝不能拼 `scrollHeight`**：懒加载会让总高度持续变大，拼进 key 会被误判成“切换列表”而每加一屏就 `scrollTop=0` 反复回顶，永远滚不到底（现象：滚一会儿又从头开始，条数停在 ~105）。
- **网页内伪造 `KeyboardEvent(keydown/PageDown)` 不会触发浏览器默认滚动**，所以直接改 `scrollTop`，等效且快得多。
- 改了注入 JS 必须重新 `go build` 并重启代理；**已打开的视频号页是在旧 JS 下加载的，必须刷新/重进一次新 JS 才生效**。
- 仅滚动列表（不逐条点开播放）就能让翻页 API 返回带 `decode_key` 的 media 数据，这是全自动可行的决定性事实。

实测「交易的游戏」（=公众号顶底之王）：刷新后约 1 分钟抓到 **339 个真实短视频（均带 decode_key 换签直链）+ 27 个直播回放（明文直链）**。

### 2.2 合并、去重与对账

- `-output` 文件是代理**追加写的多段 JSON 拼接**（不是单个合法 JSON 数组），解析要用 `JSONDecoder.raw_decode` 从偏移量循环读出多个块再展平。
- 多次捕获取并集：短视频以有 `decode_key` 为准、按 URL 的 `encfilekey` 去重；回放按无 `decode_key` 且 `stodownload`、体积 >30MB 归类，同样按 `encfilekey` 去重。
- 与历史清单（如 `shorts_*_slim.json`）对账：主键用 `encfilekey`，并用 `md5` 交叉验证。
- **数量对不上的常见原因不是漏抓**：0 秒、`durMs/videoPlayLen=0`、`specs=[]`、仅几百 KB 的条目 `mediaType=2` 是**图文/图片动态，不是视频**，视频流采集中本就不会出现。本次 340 清单与 339 视频的唯一差额正是此类。
- 直链 Range 抽验返回 `206` 即可下；token/svrnonce 有时效，抓完尽快下载，过期重新刷新换签。

---

## 3. 下载与解密（✅ 2026-09-21 端到端验证通过）

> 完整算法、wasm 契约、验证证据、规格/md5 口径见权威文档：[`../research/wechat-short-video-decryption.md`](../research/wechat-short-video-decryption.md)

1.  短视频（Isaac64 加密，仅前 128KB）：批量脚本自动完成。以捕获到的 `decode_key`（9–10 位数字串）为 seed，经官方 wasm `WxIsaac64` 生成 131072B 密钥流（内部已 reverse），与文件前 128KB 逐字节 XOR，其后明文。
2.  直播回放：明文 MP4，无需解密，直接下载。
3.  有效性校验：偏移 4 处为 `ftyp`（脚本自动），并可 ffprobe 核对时长/分辨率；脚本同时做 md5 对账。
4.  规格口径：换签直链默认返回 xWT112 标清；捕获记录的 `size/md5` 多为 best_format 高清，默认 URL 下载后 md5 不一致属**规格差异非失败**。要高清加第 5 位置参数 `max`（xWT111），详见 research/video-quality-url.md。
5.  时效：换签 URL 含 token/svrnonce，**捕获后尽快下载**，过期需重新播放/滚动捕获。
6.  代理：下载默认直连（国内 CDN）；如需走捕获代理设 `WC_PROXY=http://127.0.0.1:8899`；先用 `WC_LIMIT=1` 小批量验证。

```bash
DL=platforms/wechat_channels/video-downloader/batch_download_v4.py
WC_LIMIT=1 python3 $DL platforms/wechat_channels/video-capture/capture_shortprobe.json /tmp/dl short   # 先验1条
python3 $DL <capture.json> <outdir> short                                                              # 全量短视频
python3 $DL <capture.json> <outdir> live                                                              # 直播回放(明文)
```

### 3.1 补缺下载与落库规范（2026-09-21 端到端验证）

新账号/补齐存量时按本节执行，不要把目录、质量、过滤写死在命令里。

- **落库目录（参数化，不写死）**：`library/01_video/<domain>/<account>/{short,live}/`。`domain`/`account` 来自 `config/sources.json`（如 stock/交易的游戏）；`outdir` 是 `batch_download_v4.py` 的第 2 位置参数，新源只改配置与入参、不改代码。原始文件 gitignore、不进公有仓。
- **默认质量 = min（知识型偏小）**：股票/知识型内容最终转文字，第 5 位置参数用 `min`（xWT128，单条短视频 2–4MB、回放约为记录的 1/3）。只有珠宝/艺术品等需高清时才显式指定 `max`。
- **自动过滤图文动态**：下载前必须过滤非视频条目，判定规则 = **无 `decode_key` 或时长 ≤3 秒**（即 §2.2 的 `mediaType=2`、0 秒、`specs=[]` 图文动态），不下载、不计入数量。
- **对账口径**：
  - 短视频按标题对齐——现有文件名形如 `short_NNN_正文_标签1_标签2.mp4`，**取去序号前缀后第一个 `_` 之前的正文段**再归一化（去 `#标签`/标点/空白）；不要把 `_` 当标点删，否则正文与标签粘连。
  - 直播回放同名多（"回调就是进场机会"等），不能按标题去重；按**完整下载后文件字节数**对清单 `size`（容差 2%）匹配。
- **编号续接与断点**：新补文件从现有最大编号 +1 开始（避免重号）；后台长任务中断（exit -1 多为任务被回收、非下载错误）时，用 `nohup ... &` 脱离会话，按已成功条数切片续跑，不要从头重下。
- **台账**：落库后生成 `library/00_manifest/<account>_inventory.json`，登记每条的 seq/文件名/标题/时长/磁盘大小/encfilekey，支撑增量水位与后续同步。

---

## 4. 视频号特有问题
| 问题 | 解决 |
|---|---|
| 微信不走代理 | video-capture自动对所有活动网络服务设置代理，无需手动 |
| 短视频无法播放 | 短视频需要解密，批量下载脚本自动处理 |
| DecodeKey获取位置 | 捕获数据中的`decode_key`字段 |
| 直播回放是否需要解密 | 不需要 |
| 下载的视频只有2-5MB | **不是缺陷**：知识型内容默认 min 偏小(2-4MB)是预期目标（最终转文字）；只有珠宝/艺术等需高清才加第5参 `max` |

---

## 5. 参考
- 微信基础操作：[wechat-basic-operations.md](wechat-basic-operations.md)
- 公众号采集：[wechat-official-article.md](wechat-official-article.md)
- **短视频解密（已验证权威结论）**：[`../research/wechat-short-video-decryption.md`](../research/wechat-short-video-decryption.md)
- 视频质量URL研究：[`../research/video-quality-url.md`](../research/video-quality-url.md)
- 解密器源码：`platforms/wechat_channels/video-downloader/wechat_decrypt.js`、`batch_decrypt.js`（自包含 wasm2js `decrypt_node.js`）
