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
| T-09 | 高质量URL研究 | research | 无 | **done** | xWT111比默认大69%，`docs/RESEARCH-video-quality-url.md` |
| T-10 | 视频号API研究（方案B） | research | 无 | **todo** | 证书路径已修复，可重新测试 |
| T-11 | 项目治理与文档架构 | refactor | 无 | **done** | DOCUMENTATION_MAP、DIRECTORY_STRUCTURE、ADR、工程记忆、WORKFLOW、REQUIREMENTS |
| T-12 | 捕获工具证书路径修复 | bugfix | 无 | **done** | 改为相对于可执行文件的路径，已验证 |
| T-13 | _workspace运行时工作区设计 | refactor | 无 | **done** | logs/tmp/capture(manifest,state)，`workspace/README.md` |
| T-14 | 知识库汇总生成 | feature | T-08 | **done** | 336个视频知识提取完成（313短视频+23直播回放），`knowledge_base_summary.json`，看涨149/震荡135/看跌52 |
| T-15 | 增量采集机制完善 | feature | T-01/T-02/T-03 | **done** | watermark接入pipeline，at-least-once，commit 3438e05 |
| T-16 | 百度网盘同步 | feature | 无 | **done** | 全部完成0失败：转写673/知识340/文章1188/短视频313/直播23/书籍6，`scripts/netdisk/sync_stock.sh` |
| T-17 | 书籍精华提取 | feature | T-03 | **done** | 4本书精华文稿完成（股票大作手回忆录/十年一梦/股剩是怎样炼成的/趋势交易法），`library/07_books/精华/`，含四书对比和量化启示 |
| T-18 | 架构重构阶段1：改名+代码迁移 | refactor | 无 | **done** | multiplatform-content-pipeline，commit bd45204，见ADR-004 |
| T-19 | 架构重构阶段2：数据迁移 | refactor | T-18 | **done** | commit 782ba97：data/videos→library/01_video，data/transcripts→library/04_transcript，knowledge-base→library/06_articles，清理空目录，更新5个脚本+5个文档路径 |
| T-20 | 架构重构阶段3：接入B站采集 | feature | T-19 | **done** | commit a24d70a：迁移bili_list.py（wbi+dynamic双通道），适配可配置UID，输出library/00_manifest/bilibili/，dynamic通道测试验证通过 |
| T-21 | 架构重构阶段4：接入抖音/YouTube | feature | T-20 | **done** | 复用multiplatform-media-fetch技能media_downloader.py，创建platforms/douyin/README.md和platforms/youtube/README.md |
| T-22 | 方法提炼（MethodNote）LLM深度分析 | feature | T-18 | **blocked** | 框架已搭（processing/method_extraction/），目标博主「原来是陶阿狗君」，抖音反爬403无法下载视频，用户说暂时跳过，等有时间手动下载视频后继续 |
| T-23 | GitHub仓库改名 | ops | 无 | **done** | 已通过computer use完成改名，stock-knowledge-base→multiplatform-content-pipeline |
| T-24 | 评审改进批次1：清理与修正（P0） | refactor | 无 | **done** | commit b5044eb：删旧脚本+修数量+更新状态+建workspace+更新文档地图 |
| T-25 | 评审改进批次2：文档精简 | refactor | 无 | **done** | commit ee3630f：退役执行计划.md+技术方案.md+修复.gitignore |
| T-26 | 评审改进批次3：需求与知识库文档更新（P1） | refactor | 无 | **done** | commit 022ecd3：合并PRD到REQUIREMENTS+合并知识库规范+更新多平台多行业 |
| T-27 | 评审改进批次4：SOP更新 | refactor | 无 | **done** | commit 1ecfb06：视频号SOP视频质量说明+待优化项更新 |
| T-28 | 评审改进批次5：内容去重（P2） | refactor | 无 | **done** | commit 9582a05：解密原理去重+修复architecture-tool-runtime过时内容 |
| T-29 | 评审改进批次6：代码质量与行业最佳实践（P2/P3） | refactor | 无 | **done** | commit 0f02eb2：修复6个硬编码路径+创建normalization标准化引擎 |

---

## 关键口径（指针，不展开）

- **视频解密原理**：DecodeKey → ISAAC64生成128KB数组 → XOR文件前128KB → 见工程记忆 `workflow-video-capture`
- **高质量URL参数**：X-snsvideoflag=xWT111（最大3.92MB）→ 见 `docs/RESEARCH-video-quality-url.md`
- **证书与代理方案**：相对于可执行文件的路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall，9.7x实时 → 见 `processing/transcription/tools/`
- **OCR工具**：macOS Vision编译二进制，1.5秒/张 → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码+文档) / 本地(视频+转写稿) / U盘(备份) / 百度网盘(镜像) → 见 ADR-001

---

## 下一步（按优先级）

> **2026-09-16 更新：直播回放转写+知识提取全部完成，知识库汇总生成，推进百度网盘同步和书籍精华提取**

1. **GitHub仓库改名**（T-23，需用户手动在网页Settings→Rename操作）
2. **百度网盘同步**（T-16，脚本已存在，待正式运行）
3. **书籍精华提取**（T-17，4本书清单已提取，待找电子书内容）
4. **方法提炼**（T-22，blocked，等用户手动下载抖音视频后继续）
5. **2篇公众号文章补采**（"每年12月哪个板块涨的最好？"和"冬至快乐"无正文）
6. **高质量URL原始版本研究**（当前2-5MB/个，真正原始48.5MB待找）

---

## 评审改进完成记录

> 来源：`project-management/reviews/2026-09-15-post-refactor-review.md`
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

## T-30 珠宝知识库合并（2026-09-16）

**状态**: ✅ 完成

**内容**: 将独立的 gemology-kb 项目（宝石学家老许B站知识库）完整合并入主仓库，后续珠宝独立项目废弃。

**合并成果**:
- 视频：743个（约13GB）→ `library/01_video/bilibili/宝石学家老许/`
- 转写稿：743个 → `library/04_transcript/bilibili/宝石学家老许/`
- 知识成品：777个 → `library/05_knowledge/concepts/`（videos 765 + topics 11 + reports 1）
- 图文动态：202个 → `library/06_articles/bilibili/宝石学家老许/`
- 外部源：8个（生财有术珠宝社区）→ `library/08_sources/community-scys-jewelry/`
- 台账：6个 → `library/00_manifest/bilibili/`
- B站脚本：17个 → `platforms/bilibili/`
- OCR脚本：4个 → `processing/ocr/`
- 文档：7个 → `project-management/jewelry-*.md`

**架构决策**:
- 平台能力通用化（platforms/bilibili/），不绑定珠宝
- 行业内容隔离（domains/jewelry/）
- 数据按平台+账号组织（library/01_video/bilibili/宝石学家老许/）
- 配置驱动（config/sources.json添加B站源）

**网盘同步**: 已启动珠宝视频/转写/知识成品同步到百度网盘「珠宝知识库/」

**下一步**:
- 珠宝视频同步完成后验证网盘完整性
- 统一网盘同步脚本（sync_library.sh已创建，支持多知识库）
- 清理旧的 sync_stock.sh（可保留为别名）

## T-31 指定博主全量采集（通用能力）

**状态**: todo（处理完书籍转码后启动）

**需求来源**: 用户提供两个抖音博主，需要全量采集视频和图文。

### T-31A 珠宝学者郭颖（珠宝行业专业博主）
- **平台**: 抖音
- **抖音号**: 63296316022
- **身份**: 中国地质大学（北京）珠宝学院院长、教授、博士生导师
- **粉丝**: 11.2万
- **作品**: 378个
- **需求**: 下载所有视频和图文，作为珠宝行业知识库补充
- **行业**: jewelry
- **前置**: 抖音采集能力（T-21已接入，但抖音反爬403需解决）

### T-31B 原来是陶阿狗君（广告/创意博主）
- **平台**: 抖音
- **链接**: https://v.douyin.com/6Tb0LYRlr6s/
- **需求**: 下载所有视频和图文 + 分析拍摄技巧、AI使用效果、内容呈现风格，提炼可复用的生成方法
- **特殊性**: 除采集外还需要方法提炼（与T-22方法提炼合并）
- **前置**: 抖音采集能力 + 方法提炼LLM分析

### 通用能力建设
- 统一的"指定博主全量采集"流程：输入平台+博主ID → 列表获取 → 视频下载 → 图文采集 → 转写 → 知识提取
- 抖音反爬问题需解决（当前yt-dlp 403）
- 采集结果按平台+账号+行业组织（与现有架构一致）

## T-32 艺术/博物馆参考站点采集（珠宝行业知识补充）

**状态**: todo

**需求来源**: 用户提供博物馆和艺术类站点清单，用于珠宝行业知识库的艺术/设计参考补充。

**站点清单**（仅"博物馆和艺术"大类）:

| 站点 | 说明 | 用途 |
|---|---|---|
| artsandculture.google.com | 在家逛世界各大博物馆 | 珠宝设计灵感、艺术史参考 |
| rijksmuseum.nl | 高清艺术作品可下载 | 荷兰黄金时代珠宝/装饰艺术 |
| metmuseum.org | 大都会开放藏品 | 古代珠宝、首饰藏品高清图 |
| wikiart.org | 25万件艺术作品 | 艺术风格、色彩搭配参考 |
| publicdomainreview.org | 被历史遗忘的视觉宝藏 | 古董珠宝、历史装饰图案 |
| europeana.eu | 欧洲文化遗产档案 | 欧洲各国珠宝历史藏品 |

**采集计划**:
- 优先采集与珠宝直接相关的藏品（首饰、宝石、装饰艺术）
- 高清图片下载 + 藏品说明文字提取
- 按主题分类（古代珠宝/近现代首饰/设计灵感/宝石学）
- 作为珠宝知识库的"艺术参考"子目录

**前置**: 需评估各站点的爬虫友好度和使用条款

## T-33 视频/图文提到的书籍收集（股票行业）

**状态**: 进行中（《金融炼金术》✅完成，《广义趋势理论》⏳待用户决策）

**需求来源**: 公众号277篇文章中提到6本书，需收集电子版并转码。

### 已完成
| 书名 | 状态 | 来源 | 转码结果 |
|------|------|------|----------|
| 股票大作手回忆录 | ✅ | 网上下载 | extracted/stock/ |
| 十年一梦 | ✅ | 用户提供 | extracted/stock/ |
| 股剩是怎样炼成的 | ✅ | 用户提供（扫描件OCR） | extracted/stock/ |
| 趋势交易法（鹿希武） | ✅ | 用户提供 | extracted/stock/ |
| 金融炼金术（索罗斯） | ✅ | GitHub 0voice/expert_readed_books（PDF+mobi） | 196,179字符，extracted/stock/金融炼金术-索罗斯_extracted.md |

### 待决策
| 书名 | 调查结果 | 选项 |
|------|----------|------|
| 广义趋势理论 | ❌ **不是出版书**，是顶底之王自己的内部付费视频课程（11讲）。爱雅微课（ke.iya88.com/17248.html）有百度网盘下载，但需付费9.9元。课程目录：进场点找法/实战/精确点位/支撑阻力/第二种进场点/第三种找法/实战问题/A股终极阻力等 | A. 付费9.9元获取百度网盘链接下载视频课程 B. 放弃（因为是视频课不是书，且顶底之王视频号已有大量免费视频） C. 用户自行决定 |

### 课程目录（广义趋势理论，11讲）
1. 第一讲：进场点的找法
2. 第二讲：实战
3. 第三讲
4. 第四讲：如何精确点位
5. 第五讲：精确点位个股实战演练
6. 第六讲：支撑阻力力度
7. 第七讲：第二种进场点找法
8. 第八讲：第三种找法以及买卖中的一些细节
9. 第九讲：实战中遇到的各种问题细节
10. 第十讲：A股终极阻力在哪，以及这两个月怎么走
11. 第十一讲：广义趋势理论细节

**下一步**: 用户决策《广义趋势理论》是否付费获取 → 完成后启动书籍知识详解生成
