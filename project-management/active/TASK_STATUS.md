# 任务状态台账（TASK_STATUS）

> **文档类型**：Status（状态台账，动态更新）
> **更新频率**：每个子任务完成时、遇到阻塞时
> **本页是"当前做什么、到哪"的唯一进度真相**
> 需求溯源看 `docs/REQUIREMENTS.md`，开放缺陷看 `project-management/active/ISSUES.md`
> 稳定结论的权威版在 ADR / 工程记忆，本页只放指针、不复制结论

---

## 当前进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| ① 资源采集 | 进行中 | 视频号权威全集 **340短视频/29回放/1图文**（catalog 09-23），磁盘 340+29 全有、去重干净（ISSUE-016/017 已闭环）；公众号文章待全量导出 |
| ② 内容处理 | ✅ 完成 | 转写 **340+29 全齐**（含 09-23 新增 live_029），图文 OCR ✅ |
| ③ 知识提取 | 进行中 | 规则版已完成，LLM深度提取待接入 |
| ④ 知识库组织 | 方案就绪 | 待执行 |
| 项目治理 | ✅ 完成 | 文档架构、ADR、工程记忆、SOP |

---

## 进行中/待办工单

| 编号 | 标题 | 类型 | 状态 | 说明 |
|------|------|------|------|------|
| T-10 | 视频号API研究（方案B） | research | ✅ B方案验证成功 | 列表不走HTTP，走XWEB桥+Pinia；**已验证直接调 `profile.fetchMoreData({username})` 翻页到 noMore、回放切tab首屏即全量，不滚DOM**。实测340视频+1图文/回放29（09-23 增量后）。✅ 2026-09-22 已用 ffprobe 严格对账（audit_disk.py）：短视频339全有/0缺/71重复、回放缺3，权威基准落 `library/00_manifest/catalog_交易的游戏.json`，报告落 `audit_交易的游戏.json` |
| T-22 | 方法提炼（MethodNote）LLM分析 | feature | blocked | 框架已搭；郭颖 6 个测试视频已下载转写，LLM 分析可对已转写样本先行；全量待批量下载后继续 |
| T-31 | 指定博主全量采集（郭颖） | feature | 进行中 | **2026-10-09 高价值科普知识文档化完成**：192/192 视频全转写（transcript 入库）；高价值科普 **145 条**归并为 **13 份品类知识文档**（钻石、翡翠、和田玉、彩色宝石×2〔贵重/常见与平替〕、综合文化、水晶、珍珠、黄金贵金属、南红玛瑙、绿松石、蜜蜡琥珀、有机宝石化石、青金石），已 commit/push；早期 6 份单主题文档保留、内容已并入综合稿。下一阶段：潘家园实战 46 条知识文档化（本次不做） |
| T-32 | 艺术/博物馆站点采集 | research | todo | 6个站点，待评估爬虫友好度 |
| T-33 | 视频提到的书籍收集 | feature | 进行中 | 5本完成，《广义趋势理论》待用户决策 |
| T-34 | 通用增量采集框架 | feature | ✅ 完成 | B站/YouTube验证通过；视频号 `incremental_sync.py` 已于 09-23 实跑成功（对账补下 live_029） |
| T-35 | 视频号短视频换签直链+Isaac64解密闭环 | feature | 进行中 | ✅解密算法与工具链已端到端验证（见 docs/research/wechat-short-video-decryption.md）；slim() 已补 urlToken/decodeKey/cdnFileSize/hlsSpec + 新增 probeSignActions（RLIST_ACTSRC），go build 通过；**ISSUE-017 已闭环（09-22）：一次刷新全量换签、urlToken/decodeKey 全覆盖**，近100%即一次刷新拿全，否则据 ACTSRC 对缺签条目逐条换签；best_format高清md5对账（ISSUE-003）后做 |
| T-36 | 去重/补3场回放/台账重建 | feature | ✅ 完成 | ISSUE-016 已闭环（09-22）；方案见 `wechat-channels-dedup-and-inventory.md`（ISSUE-016）：刷新换签→补3场回放+转写→用户确认后删71重复视频并同步去重转写→按catalog id重建inventory至audit全0 |

---

## 下一步（按优先级）

> **2026-09-23 更新：视频号「交易的游戏」已全量闭环——340 短视频 / 29 回放全部下载、转写，audit 缺/重/游离/歧义全 0，inventory 重建。下一步首要 = 公众号文章全量导出（需用户 GUI 配合触发拿凭证一次，之后全自动）。新会话从这里接手。**

1. **公众号文章全量导出（HTTP API，待实测）**：`profile_ext?action=home` 激活拿 `__biz/appmsg_token/pass_ticket`，再 `action=getmsg`（offset 取返回的下一页值、count=10、offset 不变即到底）；专档 `project-management/active/wechat-article-full-export-task.md`；人工只触发拿 token 一下，之后全自动。
   - 若标准 HTTP 路线仍不通，参考 wechat-article-exporter 作者付费版的取凭证方法：https://wechat.zoro.build/guide/first-sync （SPA，需 Chrome 渲染）。
   - ✅ 已完成前置：ISSUE-017 一次刷新全量换签、ISSUE-016 去重/补回放/台账重建（视频号 340/29 全齐）。
2. **百度网盘统一重新同步**（用户明确暂停，等所有前置解决后统一执行；股票/珠宝各开应用，视频原片曾出现空目录需检查，直播回放同步位置待核）
3. **股票书籍知识详解 + 《广义趋势理论》《金融炼金术》**：用户称已拿到两本电子版、晚点提供；桌面 `~/Desktop/股票书籍/` 10 个 PDF/PPTX，扫描件走 RapidOCR（work-doc-extract 技能，Python3.12 venv）；电子资料单独目录统一放、梳理后进知识详解，珠宝同理形成 SOP
4. **高质量URL原始版本研究**（当前 min 2–5MB/个，真正原始 48.5MB 待找，ISSUE-003，best_format md5 对账）

---

## 关键口径（指针，不展开）

- **视频解密原理（✅已验证）**：decode_key→WxIsaac64 生成128KB密钥流(reverse)→前128KB XOR → 见 `docs/research/wechat-short-video-decryption.md`（工具：`platforms/wechat_channels/video-downloader/`）
- **高质量URL参数**：X-snsvideoflag=xWT111 → 见 `docs/research/video-quality-url.md`
- **证书与代理方案**：相对可执行文件路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall（共享venv `~/.venvs/funasr`）→ 见 `docs/guides/audio-transcription.md`，批量脚本 `platforms/wechat_channels/video-transcribe/batch_transcribe.py`
- **OCR工具**：macOS Vision → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码) / 本地library(数据) / 百度网盘(镜像) → 见 ADR-001

---

## 最近完成（2026-09-23）

- ✅ **视频号「交易的游戏」增量收尾（全量闭环）**：重跑全量捕获（action 驱动翻页 + 换签），catalog = 340 短视频 / 29 回放 / 1 图文（mediaType=2 已过滤）。脚本现算对齐 inventory/catalog/磁盘：短视频 340 磁盘/转写全有（台账文字 339 为滞后口径）；唯一新增为回放 live_029。
- ⬇️ incremental_sync.py 实跑：补下载 live_029「上涨中继」（2182s、190.3MB 明文 MP4，ftyp 校验通过，md5 `6eecb32403c1`，直连），FunASR 转写 28646 字。
- 🧮 audit_disk：短视频 340/340、回放 29/29，缺/重/游离/歧义全 0；rebuild_inventory 重建台账（short 1804MB / live 6296MB，转写 340+29 全齐）。原料（视频/转写）按 .gitignore 不入库，仅台账（catalog/audit/inventory）入库。

---

## 最近完成（2026-09-22）

- 🔐 **ISSUE-014 凭证明文历史清除（filter-repo 全历史重写 + 强推）**：全历史扫描锁定敏感面（明文口令、被跟踪的 `.secrets/baidu_credentials.enc`、3 个含真实签名直链的捕获 JSON；无 PAT/私钥/百度 token 明文，"AKIA" 为 wasm 误报）；`.gitignore` 收紧为**整个 `.secrets/` 不入库**、`.enc` 本地持有（仓外备份 `~/.config/content-pipeline/.secrets/`）；体检弱口令检测改字面量拼接；`git filter-repo --replace-text + --invert-paths` 重写全部提交并 `--force` 强推（旧 HEAD `146e007` → 新 HEAD `55596ef`）；本地与"从 GitHub 全新克隆"双路全历史 grep 口令/PAT/私钥/真实票据均 **0 命中**，py/sh/go 构建与体检全过（0 ERROR/0 WARN）。
  - **残留动作（非阻塞）**：①建议重新走百度 OAuth 授权作废旧 token（口令用户选择不改，这是最有效补救；refresh_token 约 10 年，重新授权是否立即作废旧 refresh 未实测）；②确认新仓无误后删除桌面兜底 `mcp-PRE-CLEANUP-20260922.bundle`（含原始敏感历史）；③其他机器的旧克隆需删除重克隆。详见 ISSUE-014。
- 🧮 **视频号文件盘严格对账 + 全量基准落库（方案 A 离线收尾）**：固化 `parse_capture_log.py`（重组 captor `_api.log` 的整块/分块 payload，产出脱敏 catalog + 含票据 signed 两份分离，复刻 id=md5(md5sum)[:16]）与 `audit_disk.py`（ffprobe 时长+归一化标题+hashtag 消歧，文件盘 vs catalog 对账，带时长缓存）。权威基准落 `library/00_manifest/catalog_交易的游戏.json`（339 短视频/28 回放/1 图文，零签名）、报告落 `audit_交易的游戏.json`。结论：**短视频 339 全有、0 缺、0 游离、71 组各 2 个重复（71 个多余、约 300MB）；回放 28 缺 3、0 重复**。多匹配 short_055/short_311 已用 hashtag 消歧为两条不同视频。修复 incremental_sync.py 三处 `live`→`lives` 键 bug（待 dry-run）。改 replay_list_hook.go slim 增换签字段 + probeSignActions（go build 通过，待刷新验证 → ISSUE-017）。去重/补回放/台账重建方案见 ISSUE-016。

---

## 最近完成（2026-09-21）

- ✅ **新窗口接手闭环建成（对标 astock-quant）**：新增 `docs/项目维护SOP.md`（SSOT 路由/维护节奏/冷启动六问/提交检查）、`docs/新窗口接手开场白.md`（开窗触发词+收口四步+标准句+六问验收+换机兜底）、`docs/HANDOFF.md`（30秒画像+倒序日志+当前纠结+产物地图）、`scripts/doc_health_check.py`（核心文件/断链/登记/禁入内容/明文凭证检查，0 ERROR 才提交）；AGENTS §1.1 冷启动六问、§2.7 体检门，README「🚑新会话快速恢复」，DOCUMENTATION_MAP 全部登记
- 🔧 **体检首跑 43 ERROR 全部清零（复检 0 ERROR / 0 WARN）**：修复 docs/README 8 条旧文件名断链、design 文档 3 条缺 `../`、memory/index 3 个不存在的幽灵 concept 链接、解密研究文档漏登记；珠宝知识成品 videos 下 20 个 md 相对链接多一层 `../`（`../../topics/`→`../topics/`）；**4 个网盘脚本明文解密口令止血（改环境变量强制）→ ISSUE-014 已于 2026-09-22 filter-repo 全历史清除并强推（见上"最近完成 2026-09-22"）**；sync_netdisk.sh 疑高顿遗留见 ISSUE-015
- ✅ **T-10 B方案（Pinia action 驱动）端到端验证成功**：注入脚本直接调 `profile.fetchMoreData({username})` 翻短视频到 `noMore`、切"直播回放"tab 后 `liveCardObjects` 首屏即全量，**不滚 DOM**。交易的游戏实测 cardObjects 340（339视频 mediaType=4 + 1图文 mediaType=2）、liveCardObjects 28，oid/nid 双唯一零重复，纯视频339与旧滚动manifest精确一致（回放多1为新增）。代码 `replay_list_hook.go:actionDrive()`，结论落 api.md §6.2 / capture SOP §2.1。待办：把 action 全量接入下游下载管道（decode_key 沿用 -short-probe）、按339权威值重对账落库410口径
- ✅ **T-10 视频号API深挖完成**：列表不走HTTP，走XWEB原生桥(postMessage)+Vue Pinia状态树；凭证在主页URL(username+exportkey+pass_ticket)；结论落 docs/research/wechat-channels-api.md §6
- ✅ **视频号增量脚本** `platforms/wechat_channels/video-downloader/incremental_sync.py`：按 encfilekey(=捕获id) 对账，dry-run验证通过，只下新增差集，待实跑
- ✅ **凭证最短路径+人机协作边界**：视频号=人工点进主页即拿凭证；公众号=人工激活文章链接拿appmsg_token；"人工触发一次拿token+脚本全自动"原则落 docs/guides/wechat-channels-capture.md §6/§7
- 📄 **公众号文章HTTP API方案**：getmsg翻页参数已调研（__biz/offset/count/appmsg_token/pass_ticket），任务文档 project-management/active/wechat-article-full-export-task.md（公号三刀v1.1.0路径），待实测

- ✅ FunASR 批量转写全量完成：短视频 410 + 直播回放 25 = 435 份转写稿，0 失败，仅 1 个纯配乐空稿（short_411，有音轨无人声）。产物 `library/04_transcript/stock/交易的游戏/{short,live}/<标题>/transcript.md`
- ✅ 环境搭建：共享 venv `~/.venvs/funasr`（funasr1.4.3/torch2.2.2/torchaudio2.2.2，Intel x86_64；llvmlite 用 `--only-binary` 预编译解决源码编译坑）
- ✅ 新增 SOP `docs/guides/audio-transcription.md` + 批量脚本 `platforms/wechat_channels/video-transcribe/batch_transcribe.py`，已入库

- ✅ 视频号短视频解密闭环端到端验证：Isaac64 算法确认（非AES、仅前128KB加密）；仓内自包含 `decrypt_node.js` 与官方 wasm 密钥流逐字节一致；完整样本解密后 h264 1080x1920+aac、时长134.86s 与记录吻合
- ✅ 下载编排 `batch_download_v4.py` 修复（解密器同目录路径、可选代理 WC_PROXY、WC_LIMIT、md5 对账、规格差异标注）
- ✅ 捕获代理 `-short-probe` 静默探针落库换签直链+decode_key（captor.go/main.go/short_probe_hook.go，go vet/build 通过）
- ✅ 安全：含签名票据的捕获产物加入 video-capture/.gitignore，旧 capture_*.json 停止跟踪；其历史痕迹已于 2026-09-22 随 ISSUE-014 一并 filter-repo 清除
- 📄 新增权威技术文档 docs/research/wechat-short-video-decryption.md，采集SOP同步更新

---

## 最近完成（2026-09-18）

- ✅ SOP瘦身：三个微信SOP从1107行减到424行（-62%）
- ✅ AGENTS/WORKFLOW通路去重：工具索引精简，常见问题去重，章节引用修正
- ✅ REVIEW-governance-summary瘦身：577→~120行（-79%）
- ✅ DESIGN-knowledge-base-organization瘦身：443→~130行（-71%）

---

*最后更新：2026-09-23（视频号 340/29 全量闭环：增量 live_029 补齐转写、台账重建、audit 全 0）*
