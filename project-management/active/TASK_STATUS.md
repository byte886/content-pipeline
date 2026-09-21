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
| ① 资源采集 | ✅ 完成 | 410短视频 + 25直播回放 + 278篇文章 |
| ② 内容处理 | ✅ 完成 | 短视频转写✅、图文OCR✅、直播回放转写✅（共435份FunASR稿） |
| ③ 知识提取 | 进行中 | 规则版已完成，LLM深度提取待接入 |
| ④ 知识库组织 | 方案就绪 | 待执行 |
| 项目治理 | ✅ 完成 | 文档架构、ADR、工程记忆、SOP |

---

## 进行中/待办工单

| 编号 | 标题 | 类型 | 状态 | 说明 |
|------|------|------|------|------|
| T-10 | 视频号API研究（方案B） | research | ✅ B方案验证成功 | 列表不走HTTP，走XWEB桥+Pinia；**已验证直接调 `profile.fetchMoreData({username})` 翻页到 noMore、回放切tab首屏即全量，不滚DOM**。实测339视频+1图文/回放28，与旧滚动manifest 339/27精确对账；契约/坑见 docs/research/wechat-channels-api.md §6.2、capture SOP §2.1。⚠️台账410为落库mp4口径(含累积/重复)，需按339权威值重新对账 |
| T-22 | 方法提炼（MethodNote）LLM分析 | feature | blocked | 框架已搭，抖音反爬403，等用户手动下载视频后继续 |
| T-31 | 指定博主全量采集 | feature | todo | 抖音反爬403，暂时跳过 |
| T-32 | 艺术/博物馆站点采集 | research | todo | 6个站点，待评估爬虫友好度 |
| T-33 | 视频提到的书籍收集 | feature | 进行中 | 5本完成，《广义趋势理论》待用户决策 |
| T-34 | 通用增量采集框架 | feature | ✅ 完成 | B站/YouTube验证通过；视频号增量脚本 `incremental_sync.py` 已写好（按encfilekey对账，待实跑） |
| T-35 | 视频号短视频换签直链+Isaac64解密闭环 | feature | 进行中 | ✅解密算法与工具链已端到端验证（见 docs/research/wechat-short-video-decryption.md）；清单340短视频/27回放，当前15条短视频+27回放有换签直链可闭环，余约325条短视频需滚动/播放捕获换签；best_format高清md5对账待做 |

---

## 下一步（按优先级）

> **2026-09-21 更新：视频号 B方案（Pinia action 驱动）已验证成功并入库（commit 4339a4b）。前两项是把它端到端接通的收尾，新会话从这里接手。**

1. **【视频号B方案收尾-A】action 全量接入下载管道**：从 `*_api.log` 的 `RLIST_FEED__`（slim 数组；postRaw 按 11000 字符分块，需按 `tag__<rid>__<i>__<n>__<chunk>` 重组，日志里引号被转义成 `\"` 需还原）解析出全量 manifest（339视频 mediaType=4 + 1图文 mediaType=2 / 回放28，采集视频过滤 mediaType=2）；确认 action 模式下短视频 decode_key/换签直链如何随 `-short-probe` 一并拿到（slim 的 `url`=media[0].url，核对是否已含 decode_key，否则补探针）；复用 `batch_download_v4.py` 下载、`wechat_decrypt.js` 解密。依据：capture SOP §2.1、api.md §6.2、`replay_list_hook.go:actionDrive()`
2. **【视频号B方案收尾-B】按 339 权威值重对账落库**：现 `library/00_manifest/交易的游戏_inventory.json` summary short_total=410/live_total=25 是**落库 mp4 口径**（含历史累积/重复/低清，约 150 short + 25 live 的 encfilekey 为 null）；以 action 全量 339视频/28回放为准，跑 `incremental_sync.py --apply` 核差集，决定是否回填 null encfilekey（**待用户拍板**），修正台账数字
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

## 最近完成（2026-09-21）

- ✅ **新窗口接手闭环建成（对标 astock-quant）**：新增 `docs/项目维护SOP.md`（SSOT 路由/维护节奏/冷启动六问/提交检查）、`docs/新窗口接手开场白.md`（开窗触发词+收口四步+标准句+六问验收+换机兜底）、`docs/HANDOFF.md`（30秒画像+倒序日志+当前纠结+产物地图）、`scripts/doc_health_check.py`（核心文件/断链/登记/禁入内容/明文凭证检查，0 ERROR 才提交）；AGENTS §1.1 冷启动六问、§2.7 体检门，README「🚑新会话快速恢复」，DOCUMENTATION_MAP 全部登记
- 🔧 **体检首跑 43 ERROR 全部清零（复检 0 ERROR / 0 WARN）**：修复 docs/README 8 条旧文件名断链、design 文档 3 条缺 `../`、memory/index 3 个不存在的幽灵 concept 链接、解密研究文档漏登记；珠宝知识成品 videos 下 20 个 md 相对链接多一层 `../`（`../../topics/`→`../topics/`）；**4 个网盘脚本明文解密口令止血（改环境变量强制）→ 见 ISSUE-014：口令已在 4 个历史提交进入 public GitHub，改工作区不清历史，待用户拍板改密码/是否 filter-repo 清历史**；sync_netdisk.sh 疑高顿遗留见 ISSUE-015
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
- ✅ 安全：含签名票据的捕获产物加入 video-capture/.gitignore，旧 capture_*.json 停止跟踪（git 历史清理待用户决策）
- 📄 新增权威技术文档 docs/research/wechat-short-video-decryption.md，采集SOP同步更新

---

## 最近完成（2026-09-18）

- ✅ SOP瘦身：三个微信SOP从1107行减到424行（-62%）
- ✅ AGENTS/WORKFLOW通路去重：工具索引精简，常见问题去重，章节引用修正
- ✅ REVIEW-governance-summary瘦身：577→~120行（-79%）
- ✅ DESIGN-knowledge-base-organization瘦身：443→~130行（-71%）

---

*最后更新：2026-09-21*
