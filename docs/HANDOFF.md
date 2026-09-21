# 项目日志与交接（HANDOFF）· 多平台内容流水线

> 这是一份**活的项目日志 + 需求同步**，不是一次性交接快照。
> **读者**：新接手的 AI 窗口、来了解/评估项目的人。回答三件事：**这一路怎么讨论和想过来的？为什么这么决策？现在卡在哪、做到哪了？**
> **维护**：每轮重要讨论/决策往 §1 **倒序追加一条**（最新在上，写"聊了什么→结论→为什么"）；§3 随进度更新。定稿结论编译进 ADR/memory/SOP，本文件不长期堆结论。易变数字只放台账。

---

## 0. 30 秒画像

- **是什么**：自动化下载各平台（微信公众号 / 视频号 / B站 / 抖音 / YouTube）的视频、直播回放、图文文章，经转写（FunASR）/ OCR / 知识提取，形成**按行业隔离的知识库**，并支撑文稿/视频创作与博主"方法提炼"。架构上分**平台采集插件（个性）**与**转写处理公共层**，行业（股票/珠宝）在 `domains/`、成品在 `library/`。
- **北极星**：平台可插拔、行业可隔离、采集可增量、过程可无人值守（仅"拿一次 token"需人工触发），最终为个人量化系统与自有公众号/视频号提供知识与文案底座。
- **当前主战场**：股票行业源——公众号「顶底之王」+ 其视频号「交易的游戏」（finder username 见 `config/sources.json`，不在此写临时票据）。
- **现在在**：视频号采集 **B 方案（Pinia action 驱动）已端到端验证成功**（不滚 DOM、直接枚举全量列表），正处"把 action 全量接入下载管道 + 用权威值重对账落库"的收尾；公众号文章全量走 HTTP `getmsg` 的方案已调研、待人工激活一次凭证后实测。
- **仓库**：本地 `~/Desktop/multiplatform-content-pipeline/`；GitHub `github.com/byte886/multiplatform-content-pipeline`（public，master）。

---

## 1. 项目日志（倒序，最新在上）

> 每条记：聊了什么 → 结论 → 为什么。详细技术结论见 ADR / research，这里只留过程与理由。

### 2026-09-21（深夜）· 视频号 B 方案（Pinia action 驱动）验证成功 + 接手体系建成
- **聊了什么**：旧"准 B 方案"靠注入 JS 模拟滚动触发懒加载、再深读 Pinia 状态树，能拿全量但依赖 DOM/虚拟列表、偶发回顶。用户要求沿"列表数据源头"继续深挖，做到不滚 DOM、直接枚举全量，并把仓库收尾到"只报仓库名就能接手"。
- **结论**：
  1. 枚举 profile 页 Vue3/Pinia，定位到 **`profile` store**：`cardObjects`(短视频)/`liveCardObjects`(回放)/`noMore`/`isFetchingMore`/游标，方法 `fetchMoreData`(短视频翻页)、`getLiveUserPage`(回放翻页)。
  2. 正确契约 = **`await profile.fetchMoreData({username: profile.$state.username})`** 循环到 `noMore===true`；空参 `{}` 会误置 noMore 污染状态（只拉一页），无参抛错；游标 action 内部自读、勿手传。回放切 tab 后 `liveCardObjects` 首屏即 28、`liveNoMore=true`。
  3. 实测「交易的游戏」：cardObjects 340 = **339 视频(mediaType=4) + 1 图文(mediaType=2)**，回放 28，oid/nid 双唯一零重复；纯视频 339 与旧滚动 manifest 精确一致，回放比旧 27 多 1（新增）。
  4. 建成接手体系：`docs/项目维护SOP.md`（SSOT 路由+冷启动六问+体检门）、`docs/新窗口接手开场白.md`（固定开窗 SOP+标准句）、本文件、`scripts/doc_health_check.py`；AGENTS/README/文档地图挂接。
  5. 体检首跑逼出 43 项问题并清零（复检 0 ERROR/0 WARN）：工程文档旧命名断链、memory 幽灵 concept、珠宝成品 20 处相对链接多一层 `../`；**最重要是发现网盘解密口令明文硬编码且已进 public 历史（ISSUE-014），工作区已止血改环境变量，历史清除待用户拍板**。
- **为什么**：服务端 `noMore` 给权威终止信号，比"滚到高度不增"更可靠、更快（20–30s）、天然按 mediaType 过滤图文；接手体系让仓库自描述，换窗口/换机不丢上下文；体检脚本把"断链/明文凭证/数据误入库"挡在提交前。
- **遗留**：收尾 A（action 全量接入下载管道、确认 decode_key 随 `-short-probe` 取得）、收尾 B（339 权威值 vs 落库 410 口径重对账、null encfilekey 是否回填待拍板）。commits `4339a4b`、`08e78bc`。

### 2026-09-21 · 凭证最短路径 + 人机边界 + 增量脚本 + 公众号 HTTP API 调研
- **聊了什么**：自动化能否完全无人值守；公众号文章为何本地库/抓包都拿不全。
- **结论**：①视频号不需单独拿 token——点进主页的 URL 即自带 `username/exportkey/pass_ticket`（临时、几小时过期）；确立"**人工只触发一次拿 token（搜博主→点主页/刷新/激活链接），翻页/下载/转写全自动，不追求完全无人值守**"。②写好增量脚本 `incremental_sync.py`（按 encfilekey 对账、dry-run 通过，--apply 待实跑）。③公众号文章列表走真 HTTP API `profile_ext?action=getmsg`（需 `__biz/appmsg_token/pass_ticket`，offset 取返回下一页值），调研开源 exporter 与付费版取凭证思路，待实测；专档 `project-management/active/wechat-article-full-export-task.md`。
- **为什么**：视频号列表走 XWEB 原生桥（MITM 抓不到 body）、公众号文章走真 HTTP，两条技术路线必须分开；微信登录态绕不过，人工成本压到"点一下"。
- **已否决（勿重试）**：纯 HTTP appmsg_token 抓视频号列表；公众号后台 searchbiz/appmsgpublish 老路（已封）；微信本地库直读公众号全量（仅最近 1–5 篇）；后台「超链接」抓包法（用户明确不考虑）。

### 2026-09-21 · FunASR 全量转写 + 短视频 Isaac64 解密闭环
- **聊了什么**：下载的短视频无法直接播放/转写；知识型内容要不要高清。
- **结论**：①短视频是 Isaac64 流加密（仅前 128KB），以 `decode_key`(9–10 位数字) 为 seed 经官方 wasm `WxIsaac64.generate(131072)` 生成密钥流（内部 reverse）异或解密；直播回放明文 MP4。仓内自包含解密器与官方 wasm 密钥流逐字节一致，样本解密后 h264 1080x1920+aac、时长吻合（权威文档 `docs/research/wechat-short-video-decryption.md`）。②FunASR SenseVoiceSmall+fsmn-vad 批量转写 **435 份 0 失败**（共享 venv `~/.venvs/funasr`，Intel x86_64；禁用 faster-whisper）。③知识型默认 **min 清晰度（xWT128，2–4MB/个）**，因为最终转文字；珠宝/艺术品才用 max；目录/质量/上游代理一律参数化，图文(mediaType=2)自动过滤。
- **为什么**：低清对转写足够、省流量与存储；解密在本地复现官方 wasm，不依赖黑盒。

### 2026-09-21 · 自动滚动抓全量 + 落库台账（B 方案之前的主通道）
- **聊了什么**：res-downloader 早期能抓视频但依赖全局代理、易和 ClashX 互相干扰导致断网；要自研、不影响其他程序。
- **结论**：自研 Go 捕获代理 `video-capture`（MITM，相对路径加载证书、可选上游代理、自动设/清系统代理），注入 JS 自动滚动+自动切 tab 抓全量直链（`-autoscroll -short-probe`），抓到 339 短视频换签直链 + 27 回放；落库 `library/01_video/<domain>/<account>/{short,live}/`，台账 `library/00_manifest/<account>_inventory.json`（当时口径 410 短视频 + 25 回放，系跨多次采集累积、含重复/低清/null encfilekey，**非服务端全量，待重对账**）。
- **为什么 / 教训**：全局系统代理会短暂影响 Chrome 等读代理的 GUI，iTerm/TUN 不受影响；**绝不动 ClashX**（横杠=未设系统代理，国内视频号直连不需要它，历史多次因改它断网）；停代理必须 `stop.sh` 或只 kill 监听者，禁 kill -9 / 禁 kill 全端口。

### 2026-09（更早，详见 ADR/git log）· 架构重构与治理
- 从单一"顶底之王采集脚本"重构为**多平台内容流水线**（ADR-004：platforms/processing/core/domains/library 分层、平台插件化）；确立文档架构与治理规范（ADR-001）、证书与代理方案（ADR-002）、统一运行时工作区与过程件管理（ADR-003）。
- 三个微信 SOP（基本操作 / 视频号采集 / 公众号采集）经多轮训练与瘦身；沉淀大量 UI 自动化经验（关窗布局、激活目标窗口、Cmd+F 搜索、悬停变灰+手型校验、全屏截图动态算坐标、pyautogui 统一鼠标、主窗口 vs 微信浏览器判别）。

---

## 2. 关键决策（指针，不复制论证）

| 决策 | 落点 |
|---|---|
| 多平台流水线分层、平台插件化 | `project-management/decisions/ADR-004-架构重构为多平台内容流水线.md` |
| 文档架构与治理规范 | ADR-001 |
| 视频号采集的证书与代理方案（自研 captor、可选上游） | ADR-002 |
| 统一运行时工作区与过程件（workspace 不入库） | ADR-003 |
| 视频号列表走 XWEB/Pinia、不走 HTTP；B 方案 action 契约 | `docs/research/wechat-channels-api.md` §6 |
| 短视频 Isaac64 解密、清晰度口径 | `docs/research/wechat-short-video-decryption.md`、`docs/research/video-quality-url.md` |

---

## 3. 当前纠结 / 待拍板（咨询方重点看这）

- **收尾 A（进行中，AI 可独立做）**：把 action 全量 `RLIST_FEED`（postRaw 按 11000 字符分块，需重组、日志引号被转义成 `\"`）解析成全量 manifest；核实 action 模式下短视频 `decode_key`/换签直链是否已在 slim 的 `url` 内，否则确认 `-short-probe` 探针如何一并取得；再接 `batch_download_v4.py` + 解密器。
- **收尾 B（含待拍板）**：以 339 视频 / 28 回放为权威值，重对账落库 inventory 的 410/25；跑 `incremental_sync.py --apply`；约 150 short + 25 live 的 `encfilekey=null` **是否回填需用户拍板**（首次增量可能误报）。
- **公众号全量（待人工触发）**：需用户在微信激活一次 `profile_ext?action=home&__biz=...` 拿 `appmsg_token/pass_ticket`，之后 getmsg 翻页应全自动；尚未实测跑通。
- **暂缓项**：百度网盘统一同步（用户明确等一切处理完成再同步；股票/珠宝各开应用、视频原片曾出现空目录需检查）；知识库 LLM 深度提取（用户暂缓，先只做到转写稿）。
- **等用户提供**：《广义趋势理论》《金融炼金术》电子版用户称已拿到、晚点给。
- **诚实的局限**：台账 410/25 与服务端 339/28 口径不一致尚未对齐；公众号 getmsg 路线未实测；抖音网页反爬 403（指定博主"原来是陶阿狗君"暂跳过）；B 站 subprocess 412 须直连。
- **【ISSUE-014·高优安全，待用户拍板】** 网盘解密口令曾明文硬编码在 4 个 `scripts/netdisk/` 脚本、随 4 个历史提交进入 public GitHub。工作区已止血（强制环境变量 `BAIDU_ENC_PASS`、体检拦明文），但**不清历史**：建议改密码；彻底清除需 filter-repo 重写历史强推（L2）。`sync_netdisk.sh` 疑高顿遗留 0 引用见 ISSUE-015。

---

## 4. 产物地图（想深入看哪）

| 你想深入 | 看哪 |
|---|---|
| 现在到哪、下一步、待拍板 | `project-management/active/TASK_STATUS.md` |
| 已知坑 / 阻塞 | `project-management/active/ISSUES.md` |
| 四阶段流水线与校验门 | `docs/WORKFLOW.md` |
| 视频号怎么抓（B 方案首选） | `docs/guides/wechat-channels-capture.md` §2.1 |
| 视频号 API/Pinia 技术结论 | `docs/research/wechat-channels-api.md` §6 |
| 微信窗口怎么自动化操作 | `docs/guides/wechat-basic-operations.md` |
| 公众号文章怎么采 | `docs/guides/wechat-official-article.md` + `project-management/active/wechat-article-full-export-task.md` |
| 转写 / OCR / 解密 | `docs/guides/audio-transcription.md`、`docs/guides/books-extraction.md`、`docs/research/wechat-short-video-decryption.md` |
| 采集源 / 行业配置 | `config/sources.json`、`domains/` |
| 落库的原始资源与成品 | `library/`（不入库，本地权威；结构见 DIRECTORY_STRUCTURE） |
| 全部文档与脚本索引 | `docs/DOCUMENTATION_MAP.md` |

---

> **维护规则**：新一轮重要讨论/决策 → §1 倒序追加；阶段/待决策变化 → 更新 §3；定稿结论编译进 ADR/memory/SOP。易变数字以台账与 manifest 为准，本文件不写死。
