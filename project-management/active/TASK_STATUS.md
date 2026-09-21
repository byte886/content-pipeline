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
| ① 资源采集 | 进行中 | 权威全集 339短视频/28回放（catalog）；磁盘短视频339全有（410文件含71重复）、回放缺3场（ISSUE-016）；公众号文章待全量导出 |
| ② 内容处理 | ✅ 完成 | 短视频转写✅、图文OCR✅、直播回放转写✅（共435份FunASR稿）；补回放后需补转写 |
| ③ 知识提取 | 进行中 | 规则版已完成，LLM深度提取待接入 |
| ④ 知识库组织 | 方案就绪 | 待执行 |
| 项目治理 | ✅ 完成 | 文档架构、ADR、工程记忆、SOP |

---

## 进行中/待办工单

| 编号 | 标题 | 类型 | 状态 | 说明 |
|------|------|------|------|------|
| T-10 | 视频号API研究（方案B） | research | ✅ B方案验证成功 | 列表不走HTTP，走XWEB桥+Pinia；**已验证直接调 `profile.fetchMoreData({username})` 翻页到 noMore、回放切tab首屏即全量，不滚DOM**。实测339视频+1图文/回放28。✅ 2026-09-22 已用 ffprobe 严格对账（audit_disk.py）：短视频339全有/0缺/71重复、回放缺3，权威基准落 `library/00_manifest/catalog_交易的游戏.json`，报告落 `audit_交易的游戏.json` |
| T-22 | 方法提炼（MethodNote）LLM分析 | feature | blocked | 框架已搭，抖音反爬403，等用户手动下载视频后继续 |
| T-31 | 指定博主全量采集 | feature | todo | 抖音反爬403，暂时跳过 |
| T-32 | 艺术/博物馆站点采集 | research | todo | 6个站点，待评估爬虫友好度 |
| T-33 | 视频提到的书籍收集 | feature | 进行中 | 5本完成，《广义趋势理论》待用户决策 |
| T-34 | 通用增量采集框架 | feature | ✅ 完成 | B站/YouTube验证通过；视频号增量脚本 `incremental_sync.py` 已写好（按encfilekey对账，待实跑） |
| T-35 | 视频号短视频换签直链+Isaac64解密闭环 | feature | 进行中 | ✅解密算法与工具链已端到端验证（见 docs/research/wechat-short-video-decryption.md）；slim() 已补 urlToken/decodeKey/cdnFileSize/hlsSpec + 新增 probeSignActions（RLIST_ACTSRC），go build 通过；**待用户刷新主页验证换签覆盖率（ISSUE-017）**，近100%即一次刷新拿全，否则据 ACTSRC 对缺签条目逐条换签；best_format高清md5对账（ISSUE-003）后做 |
| T-36 | 去重/补3场回放/台账重建 | feature | 待执行 | 方案见 `wechat-channels-dedup-and-inventory.md`（ISSUE-016）：刷新换签→补3场回放+转写→用户确认后删71重复视频并同步去重转写→按catalog id重建inventory至audit全0 |

---

## 下一步（按优先级）

> **2026-09-22 更新：B 方案离线全量链路与文件盘严格对账已完成并入库（parse_capture_log.py / audit_disk.py / catalog / audit 报告）。当前唯一阻塞是需要用户在场刷新一次主页验证新 hook 换签覆盖率，随后补 3 场回放、去重、重建台账。新会话从这里接手。**

1. **【需用户 GUI 一次·ISSUE-017】新 hook 刷新验证换签覆盖率**：启动新 captor（`./video-capture -replay-list -short-probe -output /tmp/x.json -upstream ""`，国内直连、绝不动 ClashX），请用户刷新/重进「交易的游戏」视频号主页（旧页跑旧 JS，必须刷新），action 自动拉全量后用 `parse_capture_log.py` 重组：看 signed_coverage，近 100% 即一次刷新拿全 decodeKey/urlToken；仅首屏带则 grep 日志 `RLIST_ACTSRC` 定位 feed/home.getObjectAsyncLoadInfo 源码与参数契约，对缺签条目逐条节流换签，二次刷新验证。
2. **【ISSUE-016】补 3 场缺回放 → 去重 → 重建台账**：拿到有效直链后用 `batch_download_v4.py ... live` 补下 3 场（ids 见 ISSUE-016）并转写；输出 71 组短视频 keep/drop 清单（keep 须解密可播放+有转写），**用户确认后**删 71 个重复视频并同步去重转写目录（省约 300MB）；按 catalog 16hex id 重建 inventory，跑 `audit_disk.py` 至缺/重/游离/歧义全 0。方案与检查点见 `project-management/active/wechat-channels-dedup-and-inventory.md`。
3. **公众号文章全量导出（HTTP API，待实测）**：`profile_ext?action=home` 激活拿 `__biz/appmsg_token/pass_ticket`，再 `action=getmsg`（offset 取返回的下一页值、count=10、offset 不变即到底）；专档 `project-management/active/wechat-article-full-export-task.md`；人工只触发拿 token 一下，之后全自动
4. **百度网盘统一重新同步**（用户明确暂停，等所有前置解决后统一执行；股票/珠宝各开应用，视频原片曾出现空目录需检查，直播回放同步位置待核）
5. **《广义趋势理论》《金融炼金术》**：用户称已拿到电子版，晚点提供
6. **股票书籍知识详解生成**：桌面 `~/Desktop/股票书籍/` 10 个 PDF/PPTX，扫描件走 RapidOCR（work-doc-extract 技能，Python3.12 venv）；电子资料单独目录统一放、梳理后进知识详解，珠宝同理形成 SOP
7. **高质量URL原始版本研究**（当前 min 2–5MB/个，真正原始 48.5MB 待找，ISSUE-003，best_format md5 对账）

---

## 关键口径（指针，不展开）

- **视频解密原理（✅已验证）**：decode_key→WxIsaac64 生成128KB密钥流(reverse)→前128KB XOR → 见 `docs/research/wechat-short-video-decryption.md`（工具：`platforms/wechat_channels/video-downloader/`）
- **高质量URL参数**：X-snsvideoflag=xWT111 → 见 `docs/research/video-quality-url.md`
- **证书与代理方案**：相对可执行文件路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall（共享venv `~/.venvs/funasr`）→ 见 `docs/guides/audio-transcription.md`，批量脚本 `platforms/wechat_channels/video-transcribe/batch_transcribe.py`
- **OCR工具**：macOS Vision → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码) / 本地library(数据) / 百度网盘(镜像) → 见 ADR-001

---

## 最近完成（2026-09-22）

- 🔐 **ISSUE-014 凭证明文历史清除（filter-repo 全历史重写 + 强推）**：全历史扫描锁定敏感面（明文口令、被跟踪的 `.secrets/baidu_credentials.enc`、3 个含真实签名直链的捕获 JSON；无 PAT/私钥/百度 token 明文，"AKIA" 为 wasm 误报）；`.gitignore` 收紧为**整个 `.secrets/` 不入库**、`.enc` 本地持有（仓外备份 `~/.config/multiplatform-content-pipeline/.secrets/`）；体检弱口令检测改字面量拼接；`git filter-repo --replace-text + --invert-paths` 重写全部提交并 `--force` 强推（旧 HEAD `146e007` → 新 HEAD `55596ef`）；本地与"从 GitHub 全新克隆"双路全历史 grep 口令/PAT/私钥/真实票据均 **0 命中**，py/sh/go 构建与体检全过（0 ERROR/0 WARN）。
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

*最后更新：2026-09-22（视频号严格对账+工具固化，ISSUE-016/017 登记）*
