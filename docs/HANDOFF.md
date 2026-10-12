# 项目日志与交接（HANDOFF）· 多平台内容流水线

> 这是一份**活的项目日志 + 需求同步**，不是一次性交接快照。
> **读者**：新接手的 AI 窗口、来了解/评估项目的人。回答三件事：**这一路怎么讨论和想过来的？为什么这么决策？现在卡在哪、做到哪了？**
> **维护**：每轮重要讨论/决策往 §1 **倒序追加一条**（最新在上，写"聊了什么→结论→为什么"）；§3 随进度更新。定稿结论编译进 ADR/memory/SOP，本文件不长期堆结论。易变数字只放台账。

---

## 0. 30 秒画像

- **是什么**：自动化下载各平台（微信公众号 / 视频号 / B站 / 抖音 / YouTube）的视频、直播回放、图文文章，经转写（FunASR）/ OCR / 知识提取，形成**按行业隔离的知识库**，并支撑文稿/视频创作与博主"方法提炼"。架构上分**平台采集插件（个性）**与**转写处理公共层**，行业（股票/珠宝）在 `domains/`、成品在 `library/`。
- **北极星**：平台可插拔、行业可隔离、采集可增量、过程可无人值守（仅"拿一次 token"需人工触发），最终为个人量化系统与自有公众号/视频号提供知识与文案底座。
- **当前主战场**：股票行业源——公众号「顶底之王」+ 其视频号「交易的游戏」（finder username 见 `config/sources.json`，不在此写临时票据）。
- **现在在**：股票视频号源已全量闭环（340 短视频/29 回放全下载+转写、audit 缺/重/游离/歧义全 0）；主战场转向**珠宝/鉴藏知识域**——郭颖 192 条已全量转写+知识文档化（T-31），A 类 46 条补采完成（T-38），正推进 **B 级（普通展示）创作对标**（首批 10 条 + 剩余 73 条续采完成）；本日完成**全仓三层评审与治理同步**（死链修复、台账刷新、heritage 总域登记、本 HANDOFF 恢复交接主通道、ADR-005 二次改名留痕）。公众号文章全量 HTTP `getmsg` 仍待人工激活一次凭证后实测。
- **仓库**：本地 `~/Desktop/content-pipeline/`；GitHub `github.com/byte886/content-pipeline`（public，master）。

---

## 1. 项目日志（倒序，最新在上）

> 每条记：聊了什么 → 结论 → 为什么。详细技术结论见 ADR / research，这里只留过程与理由。

### 2026-10-12 · 全仓评审与治理同步 + 视频资产台账入库 + 郭颖 B 级对标创作收尾
- **聊了什么**：股票源闭环后，跨窗口交接的"活态台账与实际脱节"暴露——ISSUES/TASK_STATUS/ROADMAP/REQUIREMENTS 状态滞后半月、导航 3 处死链、heritage 总域游离于治理文档、HANDOFF 停更；同时视频资产缺少统一元数据台账，郭颖 B 级（普通展示）83 条要进入创作对标。
- **结论**：①**视频资产台账入库**：`manifest.csv` 16 列字段 + 五档价值分级与 A/B/C 评级 SOP（`docs/guides/video-asset-manifest.md`）+ `scripts/xlsx_to_manifest.py` 同步对账；补全来源索引（老许 B站 744 / 交易的游戏视频号 336）；新增转写近重复普查（作品 238/唯一内容 234）与画面 dHash 普查（文本+画面双维度）。②**郭颖 B 级对标**：首批 10 条创作对标（下载转写+双轨预处理脚本入库，台账对账 248/248）→ 剩余 73 条按 6 批次（拍卖天价/明星品牌/文化寓意/原石猎奇/钻石蓝宝/玉石珍珠南红）全量续采完成，修复 `video_dual_analysis_prep.py:106` 死代码。③**全仓治理同步**：关闭 ISSUE-010/011/015、已 ✅ 项移 Closed；补登 heritage 总域三份导航；本 HANDOFF 补 10 月条目恢复交接主通道；新立 ADR-005 为二次改名留痕。
- **为什么**：台账（manifest.csv）把"大文件留本地、元数据入库"统一，跨设备恢复与对账才有单一基准；治理同步是新 AI 接手不被过期台账误导的前提——体检脚本只查结构/链接/登记，查不到"内容时效"，这部分靠人+活态台账。

### 2026-10-11 · T-37 普通展示 187 条复查 / T-38 郭颖 A 类 46 条补采 / T-39 全知识源入口
- **聊了什么**：郭颖 192 条里除科普/潘家园实战外，还有 187 条「普通展示」需逐条定级决定是否补采；A 类高优先要补；同时各知识源缺统一入口。
- **结论**：①**T-37**：187 条逐条语义分级回写台账（新增 review_grade/review_topic/review_note）= **A 补采 46 / B 可选 83 / C 不采 58**，产出《普通展示187条筛查报告.md》并为郭颖目录建入口 README。②**T-38**：按 T-37 结论补采 A 类 46 条（彩宝8/钻石11/翡翠6/和田玉5/珍珠6/黄金7/综合3），取流改用 currentSrc+`__vid` 铁证法修正预加载流串流，FunASR 转写后按 review_topic 并入对应品类文档（10-12 批4-7 归并完成）。③**T-39**：参照会计知识库范式为 `05_knowledge/` 全部知识源补导航入口，新增落地 SOP `docs/guides/knowledge-source-organization.md` 并登记文档地图。
- **为什么**：普通展示类视频价值参差，逐条人工语义定级比"一刀切全采"省流量又不漏高价值；取流铁证法（`__vid`）解决了预加载流与目标视频串流的顽疾。

### 2026-10-09 · T-31 郭颖全量采集与知识文档化完成 + 仓库二次改名
- **聊了什么**：珠宝学者郭颖博主全量采集（186/186 下载）后要转写并沉淀为结构化知识；同期用户拍板仓库名过长。
- **结论**：①**T-31**：郭颖 **192 视频全部转写零失败**并完成知识文档化，形成 17 份综合《知识文档》——145 条高价值科普归并 14 份品类文档（钻石/翡翠/和田玉/彩宝/水晶/珍珠/黄金/南红/绿松石/蜜蜡琥珀/有机宝石/青金石等）、46 条潘家园实战归并 3 份实战手册。②**二次改名**：`multiplatform-content-pipeline → content-pipeline`（英文标准术语、与体系 2 词命名风格统一），GitHub rename + remote set-url + 全链指针同步；留痕见 ADR-005。
- **为什么**：珠宝知识按品类归并成"自己话重组、带来源"的成品（OKF stable），才可对外/复用；砍掉 multiplatform 隐含属性使仓库名更地道。

### 2026-09-22 · ISSUE-014 凭证明文历史清除（filter-repo 全历史重写并强推）
- **聊了什么**：用户拍板**口令不更换**、授权清除 public 历史；并强调"不要假设攻击者拿不到密文"——口令与 `.enc` 曾同时公开，需按"百度凭证已等同泄露"处置，不能拿"密文加密了"当安全前提。
- **结论**：①全历史扫描锁定敏感面 = 明文口令（多个提交）、被跟踪的 `.secrets/baidu_credentials.enc`、3 个含真实签名直链的捕获 JSON；同时排除虚惊（无 GitHub PAT/私钥/百度 token 明文，文档票据全是占位，"AKIA" 命中是 wasm base64 子串误报）。②工作区止血：网盘脚本强制环境变量 `BAIDU_ENC_PASS`、体检拦明文、弱口令检测规则改字面量拼接（规则自身不进历史）。③`.gitignore` 收紧为**整个 `.secrets/` 不入库**（移除 `*.enc` 放行），`.enc` 本地持有 + 仓外备份 `~/.config/content-pipeline/.secrets/`。④`git bundle` 兜底后用 `git filter-repo --replace-text`（口令→`***REMOVED***`）+ `--invert-paths`（移除 `.secrets/` 与 3 个捕获 JSON）重写全部提交并 `--force` 强推（旧 HEAD `146e007` → 新 HEAD `55596ef`）。⑤本地与"从 GitHub 全新克隆"双路全历史 grep 口令/PAT/私钥/真实票据均 0 命中，`py_compile`/`bash -n`/captor `go build`/体检全过（0 ERROR/0 WARN）。
- **为什么 / 残留**：filter-repo 清不掉已存在的 fork/clone/第三方缓存，旧哈希可能短时仍可经直链访问；不改口令前提下最有效补救是**重新走百度 OAuth 授权作废旧 access/refresh token**（refresh 约 10 年；重新授权是否立即作废旧 refresh 取决于百度规则，未实测、不确定）；其他机器须重新克隆；桌面兜底 `mcp-PRE-CLEANUP-20260922.bundle` 含原始敏感历史，确认无误后删除。详见 ISSUE-014。

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
- **【ISSUE-014·安全，历史已清除，剩两个收尾动作】** 明文口令、被跟踪的 `.enc`、3 个捕获 JSON 已用 filter-repo 从全部历史移除并强推（双路复验 0 命中，详见 ISSUE-014 与 §1 的 2026-09-22 条目）。口令用户选择不改，故仍建议：①**重新走百度 OAuth 授权**作废旧 token（最有效补救，是否立即作废旧 refresh 待实测）；②确认新仓无误后**删除桌面含敏感历史的兜底 bundle**。`sync_netdisk.sh` 疑高顿遗留 0 引用见 ISSUE-015。

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
