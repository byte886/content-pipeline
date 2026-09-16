# 任务状态台账（TASK_STATUS）

> **文档类型**：Status（状态台账，动态更新）
> **更新频率**：每个子任务完成时、遇到阻塞时
> **维护者**：AI自动维护
> **读者**：AI代理和用户

> **本页是"当前做什么、到哪"的唯一进度真相**，实时更新。
> 需求溯源看 `docs/REQUIREMENTS.md`，开放缺陷看 `project-management/active/ISSUES.md`。
> 稳定技术结论的权威版在 ADR / 工程记忆，本页只放指针、不复制结论。
> 易变计数（已下多少、已转写多少）以现场成品文件为准，不抄进本页。

---

## 依赖与并行前沿

- **架构重构阶段1**：✅ 完成（改名+新目录结构+代码迁移+文档更新，commit bd45204）
- **阶段① 资源采集**：已完成（313短视频 + 23直播回放 + 277篇文章）
- **阶段② 内容处理**：短视频转写✅、图文OCR✅、直播回放转写⏳（进行中/待启动）
- **阶段③ 知识提取**：工具已开发，待批量运行
- **阶段④ 知识库组织**：方案已设计，待执行
- **项目治理**：文档架构重构✅、证书路径修复✅、workspace设计✅、WORKFLOW/REQUIREMENTS✅、架构重构✅

可并行：直播回放转写（后台运行）与架构重构阶段2（数据迁移）可同时进行。

---

## 工单清单（状态：todo / doing / blocked / done）

| 编号 | 标题 | 类型 | 前置 | 状态 | 验收 / 落点 |
|------|------|------|------|------|------------|
| T-01 | 视频号短视频采集 | feature | 无 | **done** | 313个短视频，`data/videos/短视频/` |
| T-02 | 视频号直播回放采集 | feature | 无 | **done** | 23个直播回放，`data/videos/直播回放/` |
| T-03 | 公众号文章采集 | feature | 无 | **done** | 277篇文章，`knowledge-base/02-公众号文章/` |
| T-04 | 短视频转文字 | feature | T-01 | **done** | 313个转写稿，`data/transcripts/短视频/` |
| T-05 | 直播回放转文字 | feature | T-02 | **done** | 23个转写稿全部完成，`library/04_transcript/wechat_channels/直播回放/`（成功23/失败0，2026-09-16 07:00完成） |
| T-06 | 公众号图片OCR | feature | T-03 | **done** | 910张图片OCR，更新236篇文章 |
| T-07 | 知识提取工具开发 | feature | T-04/T-06 | **done** | `processing/knowledge_extraction/tools/extract_knowledge.py` |
| T-08 | 知识提取批量运行 | feature | T-07 | **done** | 313个短视频知识提取完成，`library/05_knowledge/extracted/`（看涨145/看跌50/震荡118） |
| T-09 | 高质量URL研究 | research | 无 | **done** | xWT111比默认大69%，`docs/高质量URL研究.md` |
| T-10 | 视频号API研究（方案B） | research | 无 | **todo** | 证书路径已修复，可重新测试 |
| T-11 | 项目治理与文档架构 | refactor | 无 | **done** | DOCUMENTATION_MAP、DIRECTORY_STRUCTURE、ADR、工程记忆、WORKFLOW、REQUIREMENTS |
| T-12 | 捕获工具证书路径修复 | bugfix | 无 | **done** | 改为相对于可执行文件的路径，已验证 |
| T-13 | _workspace运行时工作区设计 | refactor | 无 | **done** | logs/tmp/capture(manifest,state)，`workspace/README.md` |
| T-14 | 知识库汇总生成 | feature | T-08 | **todo** | 按主题组织的知识库汇总 |
| T-15 | 增量采集机制完善 | feature | T-01/T-02/T-03 | **done** | watermark接入pipeline，at-least-once，commit 3438e05 |
| T-16 | 百度网盘同步 | feature | 无 | **todo** | 股票知识库应用，`scripts/netdisk/sync_stock.sh` |
| T-17 | 书籍精华提取 | feature | T-03 | **doing** | 书籍清单已提取（4本核心交易书），`library/07_books/recommended_books.json`，待找电子书内容形成文稿 |
| T-18 | 架构重构阶段1：改名+代码迁移 | refactor | 无 | **done** | multiplatform-content-pipeline，commit bd45204，见ADR-004 |
| T-19 | 架构重构阶段2：数据迁移 | refactor | T-18 | **done** | commit 782ba97：data/videos→library/01_video，data/transcripts→library/04_transcript，knowledge-base→library/06_articles，清理空目录，更新5个脚本+5个文档路径 |
| T-20 | 架构重构阶段3：接入B站采集 | feature | T-19 | **done** | commit a24d70a：迁移bili_list.py（wbi+dynamic双通道），适配可配置UID，输出library/00_manifest/bilibili/，dynamic通道测试验证通过 |
| T-21 | 架构重构阶段4：接入抖音/YouTube | feature | T-20 | **done** | 复用multiplatform-media-fetch技能media_downloader.py，创建platforms/douyin/README.md和platforms/youtube/README.md |
| T-22 | 方法提炼（MethodNote）LLM深度分析 | feature | T-18 | **blocked** | 框架已搭（processing/method_extraction/），目标博主「原来是陶阿狗君」，抖音反爬403无法下载视频，用户说暂时跳过，等有时间手动下载视频后继续 |
| T-23 | GitHub仓库改名 | ops | 无 | **todo** | API token问题，可手动在网页改名（旧URL自动重定向） |
| T-24 | 评审改进批次1：清理与修正（P0） | refactor | 无 | **done** | commit b5044eb：删旧脚本+修数量+更新状态+建workspace+更新文档地图 |
| T-25 | 评审改进批次2：文档精简 | refactor | 无 | **done** | commit ee3630f：退役执行计划.md+技术方案.md+修复.gitignore |
| T-26 | 评审改进批次3：需求与知识库文档更新（P1） | refactor | 无 | **done** | commit 022ecd3：合并PRD到REQUIREMENTS+合并知识库规范+更新多平台多行业 |
| T-27 | 评审改进批次4：SOP更新 | refactor | 无 | **done** | commit 1ecfb06：视频号SOP视频质量说明+待优化项更新 |
| T-28 | 评审改进批次5：内容去重（P2） | refactor | 无 | **done** | commit 9582a05：解密原理去重+修复architecture-tool-runtime过时内容 |
| T-29 | 评审改进批次6：代码质量与行业最佳实践（P2/P3） | refactor | 无 | **done** | commit 0f02eb2：修复6个硬编码路径+创建normalization标准化引擎 |

---

## 关键口径（指针，不展开）

- **视频解密原理**：DecodeKey → ISAAC64生成128KB数组 → XOR文件前128KB → 见工程记忆 `workflow-video-capture`
- **高质量URL参数**：X-snsvideoflag=xWT111（最大3.92MB）→ 见 `docs/高质量URL研究.md`
- **证书与代理方案**：相对于可执行文件的路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall，9.7x实时 → 见 `processing/transcription/tools/`
- **OCR工具**：macOS Vision编译二进制，1.5秒/张 → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码+文档) / 本地(视频+转写稿) / U盘(备份) / 百度网盘(镜像) → 见 ADR-001

---

## 下一步（按优先级）

> **2026-09-16 更新：架构完善（PlatformFetcher+处理链+增量采集）已完成，直播回放转写后台运行中**

1. **直播回放转写**（T-05，23个，后台运行中，4/23完成，预计还需1.5小时）
2. **GitHub仓库改名**（T-23，需用户手动在网页Settings→Rename操作）
3. **百度网盘同步**（T-16，脚本已存在，待正式运行）
4. **书籍精华提取**（T-17，4本书清单已提取，待找电子书内容）
5. **方法提炼**（T-22，blocked，等用户手动下载抖音视频后继续）
6. **知识库汇总生成**（T-14，按主题组织的知识库汇总）
7. **2篇公众号文章补采**（"每年12月哪个板块涨的最好？"和"冬至快乐"无正文）
8. **高质量URL原始版本研究**（当前2-5MB/个，真正原始48.5MB待找）

---

## 评审改进完成记录

> 来源：`docs/project-management/reviews/2026-09-15-架构重构后评审.md`
> 状态：**全部6个批次已完成**（2026-09-15）

| 批次 | 工单 | 内容 | 优先级 | 完成commit |
|------|------|------|:---:|:---:|
| 批次1 | T-24 | 清理与修正：删旧脚本+修数量+更新状态+建workspace+更新文档地图 | P0 | b5044eb |
| 批次2 | T-25 | 文档精简：退役执行计划.md+技术方案.md+修复.gitignore | P1 | ee3630f |
| 批次3 | T-26 | 需求与知识库文档更新：合并PRD+更新多平台需求+合并知识库规范 | P1 | 022ecd3 |
| 批次4 | T-27 | SOP更新：视频号SOP数量修正+视频质量说明+待优化项 | P1 | 1ecfb06 |
| 批次5 | T-28 | 内容去重：解密原理去重+修复architecture-tool-runtime过时内容 | P2 | 9582a05 |
| 批次6 | T-29 | 代码质量：修复6个硬编码路径+创建normalization标准化引擎 | P2/P3 | 0f02eb2 |

**评审核心结论**：总体⭐⭐⭐½，架构方向正确，需清理过时文档（PRD/技术方案/执行计划严重过时）和冗余内容（解密原理在14个文档重复）。

---

*最后更新：2026-09-16*
