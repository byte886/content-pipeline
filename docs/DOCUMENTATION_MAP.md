# 文档地图（DOCUMENTATION MAP）

> **文档类型**：Reference（参考资料 — 文档索引）
> **更新频率**：每次新增/删除/移动文档时

> 本文档是项目所有文档的导航入口，告诉AI和人"先读什么、去哪里找什么"。

---

## 快速入口（按场景）

### 开始新任务前
1. 开新窗口/换新窗口：直接按 `docs/新窗口接手开场白.md` 走（选项目文件夹 + 发标准句）
2. 冷启动/续接读什么、冷启动六问：`AGENTS.md` §1.1 与 `docs/项目维护SOP.md` §5
3. 最近怎么讨论过来、现在卡在哪：`docs/HANDOFF.md`（§1 倒序日志 + §3 当前纠结）
4. 当前到哪/下一步：`project-management/active/TASK_STATUS.md` + `active/ISSUES.md`
5. 提交前：`python3 scripts/doc_health_check.py`，0 ERROR 才提交

### 开发环境与 AI 编程工具
1. `docs/guides/codex-dev-environment.md` — **Codex 安装、模型选型(GPT-5.6 Sol)、算力购买(订阅/中转/国产)、配置与操作步骤**

### 技能编写与优化
> （2026-10-12 评审：`docs/guides/技能编写优化SOP.md` 该文档不存在，已移除；技能编写规范暂以各技能仓 SKILL.md 为准）

### 网络环境预检（任何改系统代理的采集前）
1. `docs/guides/network-preflight.md` — 只读网络诊断与上游代理选择（代理翻墙能力实测、Tailscale、跨机器配置）

### 微信基本操作（UI自动化）
1. `docs/guides/wechat-basic-operations.md` — 窗口管理、搜索操作、鼠标控制最佳实践

### 视频号内容采集
1. `docs/guides/wechat-channels-collect-sop.md` — **一键采集 SOP（首选，人工只开一次窗）**
2. `docs/guides/wechat-channels-capture.md` — 采集流程与手动原语（捕获→下载→解密→验证、排障原理）
3. `docs/research/video-quality-url.md` — X-snsvideoflag参数、6种格式对比
4. `docs/research/wechat-channels-api.md` — 方案B API研究记录

### 公众号文章采集
1. `docs/guides/wechat-official-article.md` — 文章采集流程

### 增量采集
1. `docs/guides/incremental-fetch.md` — 多平台内容更新发现与下载

### 电子资料处理
1. `docs/guides/books-extraction.md` — PDF/PPTX等电子资料转码与精华提取
2. **桌面书籍知识源盘点（2026-10-13）**：盘点报告 `docs/reviews/2026-10-13-桌面书籍知识源盘点.md`；分批执行方案 `docs/reviews/2026-10-13-桌面书籍分批执行方案.md`；采集台账 `library/00_manifest/桌面书籍采集台账_2026-10-13.json`（股票书籍/顶底之王/鉴藏 Y0068 三源：文件→中间物→状态）；提取产物本地持有（`library/07_books/*/extracted/`，不入 git）

### 视频转文字 / 图文OCR
1. `docs/guides/audio-transcription.md` — FunASR 本地离线转写：环境搭建、批量脚本用法、输出目录、空稿判定
2. 批量转写脚本：`platforms/wechat_channels/video-transcribe/batch_transcribe.py`（模型只加载一次、断点续跑）
3. OCR工具：`processing/ocr/tools/batch_article_images.py`（macOS Vision）
4. **智能关键帧抽取**（镜头检测+清晰度评分+dHash去重）：`~/Doubao/skills/multiplatform-media-fetch/scripts/extract_keyframes.py`（路径待核实：本仓外该 skill 内当前未定位到此文件）

### 抖音博主全量采集（2026-10-08新增）
1. 抖音平台说明：`platforms/douyin/README.md`（浏览器直读video流绕过403方案）
2. **抖音批量采集详细SOP**：`platforms/douyin/COLLECT_SOP.md`（滚动列表、分类预判、批量下载、增量更新）
3. 收集列表脚本：`platforms/douyin/scripts/collect_video_list.py`
4. 生成状态Excel脚本：`platforms/douyin/scripts/generate_excel.py`
5. 作者知识库构建通用SOP：`~/Doubao/skills/multiplatform-media-fetch/references/pipeline/author-video-knowledge-base.md`
6. 郭颖珠宝库样例：`library/05_knowledge/jewelry/珠宝学者郭颖/`
7. 郭颖 A 类补采工单（T-38 去重与进度基准）：`library/05_knowledge/jewelry/珠宝学者郭颖/郭颖A类46条补采工单.md` — 46 条待补采分 7 批（彩宝8/钻石11/翡翠6/和田玉5/珍珠6/黄金7/综合3），含浏览器取流、防风控低频串行、转写即验证、归并目标与状态流转
8. 普通展示 187 条筛查报告：`library/05_knowledge/jewelry/珠宝学者郭颖/普通展示187条筛查报告.md`（A补采46/B可选83/C不采58，分级理由）

### 视频资产台账（元数据入库，2026-10-12 新增）
1. **视频资产台账规范与价值评级 SOP**：`docs/guides/video-asset-manifest.md` — 大文件留本地、元数据入库；manifest.csv 16 列字段定义、五档价值分级＋A/B/C 评级、新增登记 / 升降级 / 跨设备恢复、xlsx→manifest 同步对账
2. 同步对账脚本：`scripts/xlsx_to_manifest.py`（xlsx→manifest.csv，自动补 md5 / 时长 / 文稿路径，硬异常非零退出）
3. 视频资产顶层索引：`library/01_video/README.md`（各来源清单与采集口径）
4. 郭颖首版入库台账：`library/01_video/jewelry/珠宝学者郭颖/manifest.csv`（387 条，其中 238 已下载并带 md5 / 时长 / 文稿路径）

### 知识提取与知识库
1. `docs/design/knowledge-base-organization.md` — 知识库架构设计+内容规范
2. **知识源组织 SOP（落地操作）**：`docs/guides/knowledge-source-organization.md` — 三层解耦、两种成品形态、目录/入口模板、draft→stable、新增博主 Checklist、交付质检清单
3. 知识层总入口：`library/05_knowledge/README.md`（珠宝 jewelry / 股票 stock 全知识源导航）
4. 行业插件模板（珠宝鉴赏/视频创作）：`~/Doubao/skills/multiplatform-media-fetch/references/domain-plugins/`
5. **数据层总入口**：`library/README.md` — library 编号体系表（00_manifest ~ 08_sources）+ 03 跳号说明 + 各目录一句话用途

### 行业知识域导航
1. **鉴藏（Heritage）总域**：`domains/heritage/README.md` — 珠宝/翡翠/古玩古董/家具/东方体系/西方体系 6 子域总表（各子域独立建包、可独立扩展；原 `domains/jewelry/` 已归入 `01_jewelry`）
2. 股票行业域：`domains/stock/knowledge_base/README.md`；珠宝成品：`library/05_knowledge/jewelry/`
3. **行业域总说明**：`domains/README.md` — jewelry（过渡保留）/ stock（旧域，仍活跃，去留待用户拍板）/ heritage（总域 6 子域）三者关系与维护纪律

### 归档文档（archive/ 只读快照）
1. `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md` — 体系架构 v1 全文历史快照（只读、不再更新）；现行权威在总控仓 control-tower，本仓 `docs/SYSTEM_ARCHITECTURE.md` 已降级为薄指针

### 遇到问题/异常
1. `grep -rn "关键词" docs/` — 搜索相关文档
2. `project-management/active/ISSUES.md` — 已知问题清单

---

## 文档完整清单

### 零、根目录标准文档（大写骨架）

| 文档 | 路径 | 用途 |
|------|------|------|
| 项目介绍 | `README.md` | 项目目标、存储分工、快速开始 |
| AI操作手册 | `AGENTS.md` | 全局执行规则、核心约束、常见问题 |
| 文档地图 | `docs/DOCUMENTATION_MAP.md` | 本文档 |
| 项目需求 | `docs/REQUIREMENTS.md` | 需求与功能范围 |
| 整体工作流 | `docs/WORKFLOW.md` | 四阶段流水线 + 各阶段校验门 |
| 目录结构 | `docs/DIRECTORY_STRUCTURE.md` | 存储分工、目录说明、命名规范 |
| 路线图 | `docs/ROADMAP.md` | 项目长期规划 |

### 一、操作指南（guides/ — 怎么做）

| 文档 | 路径 | 用途 |
|------|------|------|
| Codex开发环境与选型 | `docs/guides/codex-dev-environment.md` | Codex安装、模型选型、算力购买、配置与操作步骤 |
| 微信基本操作SOP | `docs/guides/wechat-basic-operations.md` | 窗口管理、搜索操作、鼠标控制最佳实践 |
| 网络预检SOP | `docs/guides/network-preflight.md` | 采集前只读网络诊断、代理翻墙能力实测、上游选择、跨机器配置 |
| 视频号一键采集SOP | `docs/guides/wechat-channels-collect-sop.md` | **首选**：collect_channels.py 一键，人工只开一次窗 |
| 视频号采集SOP（手动原语） | `docs/guides/wechat-channels-capture.md` | 捕获→下载→解密→验证全流程、排障原理 |
| 公众号采集SOP | `docs/guides/wechat-official-article.md` | 文章采集与OCR流程 |
| 增量采集SOP | `docs/guides/incremental-fetch.md` | 多平台内容更新发现与下载 |
| 电子资料转码SOP | `docs/guides/books-extraction.md` | PDF/PPTX等电子资料处理 |
| 视频转写SOP | `docs/guides/audio-transcription.md` | FunASR本地离线转文字：环境/批量脚本/输出/空稿判定 |
| 视频资产台账SOP | `docs/guides/video-asset-manifest.md` | 大文件本地/元数据入库：manifest字段、价值分级与A/B/C评级、登记与同步对账、跨设备恢复 |
| 知识源组织SOP | `docs/guides/knowledge-source-organization.md` | 三层解耦、两种成品形态、目录/入口模板、draft→stable、新增博主Checklist、交付质检清单 |

### 二、技术研究（research/ — 已验证的结论）

| 文档 | 路径 | 用途 |
|------|------|------|
| 高质量URL研究 | `docs/research/video-quality-url.md` | X-snsvideoflag参数研究、清晰度对比 |
| 视频号API研究 | `docs/research/wechat-channels-api.md` | XWEB/Pinia、B方案 action 契约、公众号 HTTP API |
| 短视频解密研究 | `docs/research/wechat-short-video-decryption.md` | Isaac64 流加密原理、wasm 密钥流、解密验证 |

### 三、架构设计（design/ — 方案设计）

| 文档 | 路径 | 用途 |
|------|------|------|
| 知识库组织与规范 | `docs/design/knowledge-base-organization.md` | 知识库架构设计+内容规范+标签体系 |

### 工作流设计（workflow/ — 端到端主流程）

| 文档 | 路径 | 用途 |
|------|------|------|
| 工作流目录说明 | `docs/workflow/README.md` | workflow 目录定位、与 guides/ 分工、使用规范 |
| 视频知识工作流融合规划 | `docs/workflow/视频知识工作流-融合规划-2026-10-12.md` | 博主视频→知识库→云文档：现状评估 + 目标架构（S0–S7 + 决策门 G0–G6）+ 分阶段计划（P0–P8）+ 待办登记。**后续 AI 接手入口** |
| 内容工作流主流程（详设） | `docs/workflow/workflow-main.md` | S0–S7 各阶段详设 + 决策门 G0–G6 + 多模态路由表 + 任务卡字段；与 WORKFLOW.md（概览）配套 |
| 文稿↔知识库融合桥（P3） | `docs/workflow/article-to-okf-bridge.md` | ArticleNote 形态规范 + manifest 双向指针协议 + 跨模态 src 标签协议 + 增量归并原则；**P3 批量执行完成（278 wrap + 278 原子页 + 老许 20→5 topics + fused_into 298/298，stock E0W0 / jewelry E0）** |
| 知识化统一规划（K 线） | `docs/workflow/知识化总规划-2026-10-13.md` | 博主线+书籍线统一知识化：concepts 类型词表（新增 BookNote/CourseNote）+ frontmatter 规范 + 批量 OKF 化流程 + 课程清洗门 G7 + 云同步顺序（K5）+ 任务重排（K2–K5 替代原 P4/P6；P5/P7/P8 保留）。**K2/K3/K4 已交付（2026-10-13）：books/ 220 BookNote＋课件 419 索引、courses/ 107 CourseNote、课程清洗 84 true/23 待核、fused_into 298/298、278 篇 stale_after** |
| verified/stale_after 回填规则 | `docs/workflow/verified-stale-rule.md` | 只在真实人工/来源核验处标注 verified；行情/点位类必设 stale_after；只增不删、吃不准标待核（K4 成文） |
| 评估 Agent 复查模板 | `docs/workflow/evaluation-agent-template.md` | 五维复查清单（事实/来源/一致性/覆盖/待核）+ verified/stale_after 速查表 + 规定输出格式（K4 成文，供评估轮复用） |

### 四、项目治理

| 文档 | 路径 | 用途 |
|------|------|------|
| 体系架构与路由 | `docs/SYSTEM_ARCHITECTURE.md` | 跨体系任务路由、运行机制说明 |
| 新窗口接手SOP | `docs/新窗口接手开场白.md` | 开窗触发词、老窗口收口、标准句、六问验收、换机兜底 |
| 项目维护SOP | `docs/项目维护SOP.md` | 单一真相源路由、维护节奏、冷启动六问、提交前检查 |
| 项目日志（HANDOFF） | `docs/HANDOFF.md` | 倒序过程日志（聊了什么→结论→为什么）、当前纠结、产物地图 |
| 任务状态 | `project-management/active/TASK_STATUS.md` | 当前进度、下一步（单一进度真相） |
| 问题清单 | `project-management/active/ISSUES.md` | 已知问题、阻塞项 |
| ADR决策 | `project-management/decisions/` | 架构决策记录（只增不改）；最新：ADR-006 文稿用途分型 |
| 文档治理规范 | `project-management/standards/DOCUMENTATION_PRINCIPLES.md` | 文档类型词典 + 新增内容落位决策表 + README 防则（写文档前必读） |
| 工程记忆 | `project-management/memory/` | 跨会话稳定结论编译层 |
| 文档体检脚本 | `scripts/doc_health_check.py` | 核心文件/断链/登记/禁入内容检查，0 ERROR 才提交 |

---

## 命名规范速查

| 类型 | 命名风格 | 示例 |
|------|---------|------|
| 固定名 | 原样 | README.md、AGENTS.md |
| 治理/规范/骨架 | 大写 UPPER_SNAKE_CASE | WORKFLOW.md、REQUIREMENTS.md、DOCUMENTATION_MAP.md |
| 方法/SOP/操作 | 小写 kebab-case | wechat-basic-operations.md、incremental-fetch.md |
| 脚本 | 小写 snake_case | baidu_upload.py |
| ADR | ADR-NNN-中文 | ADR-001-项目文档架构与治理规范.md |

---

*本文档随项目演进持续更新。新增文档时必须在此登记。*
