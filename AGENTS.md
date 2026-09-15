# AGENTS.md — AI代理操作手册

> **文档类型**：Governance（治理规范 — AI操作手册）
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理（每次启动自动加载）

> 本文档是AI代理的操作手册，命令式、可执行。执行任何任务前必须先阅读本文档对应部分。

---

## 1. 项目概览

**项目目标**：构建多平台内容采集与知识库生成框架，自动化采集各平台（微信公众号/视频号/B站/抖音/YouTube）的视频和图文，经过转写/OCR/知识提取后形成结构化知识库，并支持按行业（股票/珠宝等）生成文稿和视频。

**当前阶段**：架构重构阶段1已完成（commit bd45204），阶段2数据迁移待开始。

**核心数据（股票行业）**：
- 短视频：313个（已下载+转写，待迁移到library/01_video/）
- 直播回放：23个（已下载，待转写）
- 公众号文章：277篇（已下载，275篇有正文，910张图片已OCR）

---

## 2. 执行前必读

### 2.1 冷启动（首次接触/跨阶段切换）
按序读：
1. `docs/DOCUMENTATION_MAP.md` — 文档地图（快速入口，先读这个）
2. `docs/REQUIREMENTS.md` — 项目需求与决策溯源
3. `docs/WORKFLOW.md` — 整体工作流（四阶段流水线）
4. `docs/DIRECTORY_STRUCTURE.md` — 目录结构与存储分工
5. `docs/project-management/memory/index.md` — 工程记忆（跨会话稳定结论）
6. `project-management/active/TASK_STATUS.md` + `active/ISSUES.md` — 当前状态
7. 对应环节的SOP：
   - 视频采集：`docs/视频号内容采集SOP.md`
   - 文章采集：`docs/公众号文章采集SOP.md`
   - 高质量URL：`docs/高质量URL研究.md`
   - API研究：`docs/视频号API研究.md`

### 2.2 续接（继续同一阶段的任务）
只读：
1. `project-management/active/TASK_STATUS.md` — 当前进度、下一步
2. `project-management/active/ISSUES.md` — 已知问题
3. `docs/DOCUMENTATION_MAP.md` — 找到对应工具和文档
4. 该工具的README或SOP相关小节

---

## 3. 核心规则

### 3.1 证书与代理（重要！多次踩坑，已修复）

**已修复**：捕获工具现在使用**相对于可执行文件的路径**加载证书（`os.Executable()`），无论从哪个目录运行都能正确加载`platforms/wechat_channels/video-capture/ca.crt`。

**历史问题**：之前用相对路径`ca.crt`，从项目根目录运行时会生成新的未信任证书，导致TLS握手失败、全网阻断。

**正确操作**：
1. 可以从任意目录运行`./platforms/wechat_channels/video-capture/video-capture`
2. 证书路径：`platforms/wechat_channels/video-capture/ca.crt`（已在系统钥匙串信任）
3. 启动前检查：项目根目录**不应**有ca.crt/ca.key（如果有说明是旧版本生成的，删除即可）
4. 捕获完成后必须清除系统代理（工具退出时自动清除）

**紧急恢复**（如果全网阻断）：
```bash
pkill -9 -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done
```

### 3.2 工具运行目录规范

| 工具 | 路径 | 运行目录 | 原因 |
|------|------|---------|------|
| video-capture | platforms/wechat_channels/video-capture/ | 任意目录 | 已修复，使用相对于可执行文件的路径加载证书 |
| video-downloader | platforms/wechat_channels/video-downloader/ | 项目根目录 | 相对路径引用data/ |
| auto-capture | platforms/wechat_channels/auto-capture/ | 项目根目录 | 相对路径引用 |
| transcription | processing/transcription/tools/ | 项目根目录 | 相对路径引用library/ |
| ocr | processing/ocr/tools/ | 项目根目录 | 相对路径引用 |
| knowledge-extraction | processing/knowledge_extraction/tools/ | 项目根目录 | 相对路径引用 |
| article | platforms/wechat_official/article/ | 项目根目录 | 相对路径引用 |

### 3.3 问题驱动更新（强制）

发现任何问题（脚本bug、流程缺陷、文档缺失、文件位置不对）时，必须立即评估是否需要更新文档或代码，评估后必须执行，不能只发现问题不更新。

### 3.4 变更影响分级处理（强制：先确认再执行）

- **L0 顺手修复**（错字、单处断链、单文件明显小错、不牵动其它文件）：直接修复并记录到任务报告
- **L1 高扩散变更（必须先出方案、用户确认后才执行）**：批量重命名 / 跨目录移动、预计 ≥5 处引用级联、**修改命名或治理规范本身**、新增或删除"持久文档 / 机制"。必须先给"方案 + 全量影响清单"，用户确认后再动手
- **L2 架构 / 流程变更**（流程变更、架构调整、新增功能）：先和用户讨论，确认方案后再执行
- 拿不准属于哪一级时，**就高不就低**，先按 L1 出方案

### 3.5 写文档前必须检查文档组织（强制）

**遇到需要写文档、更新文档或新增内容时，必须先检查项目文档组织和分工，禁止直接写到任意文档中。**

**检查流程**：
1. 查看文档目录结构：`ls -la docs/`
2. 查找相关文档：用 `grep -r "关键词" docs/` 查找是否已有相关内容
3. 确认文档分工（见 `docs/DOCUMENTATION_MAP.md`）
4. 选择正确的文档，WORKFLOW.md只放概览和链接
5. 确保文档关联：新增或更新后，确保相关文档之间有链接

**新建持久文档前的额外门禁（防重复建设）**：先列出它要承担的每一项职责，并逐一指认现有权威源；若这些职责已被现有文档承担，则**不新建**，改为在权威源中补内容。

### 3.6 文档同步规则（强制）

每次完成阶段性任务、生成新文档、或变化项目结构时，必须按 `docs/project-management/standards/DOC_SYNC_CHECKLIST.md` 检查并同步相关文档。

**同步时机**：完成采集批次后 / 完成转写批次后 / 发现问题并解决后 / 项目结构调整后 / 大阶段完成后

**核心原则**：问题驱动更新，发现问题立即评估是否需要更新文档。

### 3.7 大任务执行状态记录（强制）

**开始任何大任务前，必须先创建执行状态记录，异常恢复时必须先读取状态记录。**

**必须创建执行状态记录的场景**：
1. 批量处理 >3 个视频/文章
2. 预计执行时间 >1 小时
3. 涉及多个工具链（捕获 + 下载 + 解密 + 转写等）
4. 用户明确要求"批量处理"、"全部完成"

**状态记录落点**：`workspace/capture/state/`（不入库），`TASK_STATUS.md` 只更新指针级状态，不抄批次明细。

**必须立即更新TASK_STATUS.md的场景**：任务开始时 / 每个子任务完成时 / 任务完成时 / 遇到问题或阻塞时 / 每次git提交前。

详细规范：`docs/project-management/standards/BATCH_TASK_EXECUTION.md`

### 3.8 清理与维护原则（强制）

**核心价值观：以精简并删除历史冗余为荣，以堆砌重复实现为耻。**

- **代码/脚本**：新增脚本前必须检查是否已有同类实现；发现 0 引用的一次性脚本、旧版已替代脚本、重复实现时，主动清理（移废纸篓带时间戳，不硬删），同步更新文档引用
- **文档**：新增文档前必须检查职责是否已被现有文档承担（见 3.5 防重复建设门禁）；发现过时文档、已废弃 SOP、重复内容时，标注退役或清理，不保留"以防万一"的僵尸文档
- **结构**：定期检查目录结构是否合理，空目录、空章节不保留
- **"不改写历史"的适用边界**：
  - **只保护编年/记录体**——ADR（`decisions/`）、git 提交历史：价值在如实记录"当时怎么定/发生了什么"，**只增不改**
  - **不保护现行规范/手册/活态台账**——AGENTS、README、WORKFLOW、REQUIREMENTS、SOP、TASK_STATUS/ISSUES：价值在"**当前正确**"，完全过期、被取代、失效的内容直接删/改
- 完成任务后检查是否有中间产物需要清理
- 不要在项目根目录散落临时文件
- **文件和目录有变化时必须检查 .gitignore**
- **提交前运行 `git status` 检查**：确认没有不该提交的文件

### 3.9 存储分工（硬约束）

| 位置 | 内容 | 说明 |
|------|------|------|
| GitHub仓库 | 代码+文档+清洗后知识成品 | **禁止**放视频、PDF、逐字转写、原文、凭证 |
| `library/01_video/` | 视频原始文件 | gitignore忽略（待从data/videos/迁移） |
| `library/04_transcript/` | 转写稿 | gitignore忽略（待从data/transcripts/迁移） |
| `library/05_knowledge/` | 结构化知识成品 | 入库（仅stable状态） |
| `library/06_articles/` | 图文原文 | gitignore忽略（待从knowledge-base/迁移） |
| `workspace/` | 过程件 | gitignore忽略 |
| 百度网盘 | 成品镜像 | 备份+跨设备访问 |

### 3.10 运行时工作区（workspace）

**过程件放在`workspace/`下**，不散落在项目根目录或/tmp/。

| 子目录 | 用途 | 保留策略 |
|--------|------|---------|
| `logs/` | 运行日志 | 中期保留（30天） |
| `tmp/` | 临时文件 | 用完即清 |
| `capture/` | 采集相关（抓包、URL清单、批次状态） | 短期保留（最近3次） |

**简化原则**：不生搬硬套高顿的6个子目录，只保留真正需要的3个。

详见：`workspace/README.md`、`docs/project-management/decisions/ADR-003.md`

---

## 4. 工具快速索引

> 完整清单见 `docs/DOCUMENTATION_MAP.md`「工具清单」

| 任务 | 工具 | 位置 |
|------|------|------|
| 视频捕获（MITM） | video-capture | `platforms/wechat_channels/video-capture/` |
| 视频下载+解密 | batch_download_v4.py | `platforms/wechat_channels/video-downloader/` |
| 自动化采集 | auto_capture.py | `platforms/wechat_channels/auto-capture/` |
| 增量采集 | incremental_collect.py | `platforms/wechat_channels/auto-capture/` |
| 视频转文字 | batch_transcribe.py | `processing/transcription/tools/` |
| 图文OCR | batch_article_images.py | `processing/ocr/tools/` |
| 知识提取 | extract_knowledge.py | `processing/knowledge_extraction/tools/` |
| 知识库查询 | knowledge_base.py | `processing/knowledge_extraction/tools/` |
| 方法提炼 | method_extractor.py | `processing/method_extraction/` |
| 文章采集 | fetch_articles_*.py | `platforms/wechat_official/article/` |
| 网盘同步 | sync_stock.sh | `scripts/netdisk/` |
| 流水线编排 | pipeline.py | `core/` |
| 增量水位 | watermark.py | `core/` |

---

## 5. 常见问题

### Q: 为什么捕获工具启动后全网断了？
A: 证书路径问题。检查项目根目录是否有ca.crt，如果有说明运行目录错了。删除根目录的ca.crt，从`platforms/wechat_channels/video-capture/`目录运行。

### Q: 视频下载后无法播放？
A: 短视频是加密的，需要用DecodeKey解密。直播回放不需要解密。运行`node platforms/wechat_channels/video-downloader/wechat_decrypt.js <decodeKey> <file>`。

### Q: 下载的视频只有2-5MB，太小了？
A: 默认是低分辨率版本。用`quality=max`参数下载xWT111格式（大69%）。真正的原始高清版本尚未找到，见`docs/高质量URL研究.md`。

### Q: 转写输出在哪里？
A: `data/transcripts/短视频/{视频名}/transcript.md`（注意是子目录，不是直接md文件）。待迁移到`library/04_transcript/wechat_channels/`。

---

## 6. 待办与已知限制

- [x] 架构重构阶段1：代码迁移+文档路径更新（commit bd45204）
- [ ] 架构重构阶段2：数据迁移到library/新结构
- [ ] 架构重构阶段3：接入B站采集（复用珠宝项目脚本）
- [ ] 架构重构阶段4：接入抖音/YouTube
- [ ] 直播回放23个尚未转写
- [ ] 方法提炼（MethodNote）LLM深度分析待实现
- [ ] 高质量URL（原始48MB版本）尚未找到
- [ ] 知识提取当前是规则版，待接入LLM深度提取
- [ ] 知识库与量化系统对接尚未实现

---

*本文档随项目演进持续更新。发现规则缺失或不准确时，按"问题驱动更新"原则立即补充。*
