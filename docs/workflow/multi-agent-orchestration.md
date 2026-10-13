# 多智能体编排 SOP（Multi-Agent Orchestration Playbook · P7 试点版）

> **文档类型**：Process / SOP（可复用、可交接、后续 AI 照做）
> **日期**：2026-10-13　**状态**：P7 试点首跑（M3/M5 升级核验干跑通过）；由真实跑通的全链路固化，不做无法落地的设计
> **归属仓库**：content-pipeline　**读者**：后续接手的 AI（编排 / 采集 / 提取 / 知识化 / 质检 / 云同步 / 审查各角色）
> **上游权威**：本 SOP 是"怎么调度"的操作层；"为什么这么设计 / 缺口登记 / 风险"以 `视频知识工作流-融合规划-2026-10-12.md` 与 `知识化总规划-2026-10-13.md` 为准，二者冲突时以规划文档待办登记为准。
> **事实纪律**：每条命令 / 脚本都给真实路径；不确定处标「待核」；禁止编造来源、数字、效果数据。

---

## 0. 一页速览（先看这张）

```
G0 选择性采集预判 ──> S1 多模态采集 ──> S2 转写/OCR/提取 ──> S3 多媒体分析（按需）
   (不主动全量采集)      (视频/音频/PDF/图片/图文)   (一律转标准中间物)        (判型命中才做)
                                                                      │
G6 云文档发布维护 <── S5 质检门 G5/G7 <── S4 批量 OKF 化 <── 文稿分型
 (draft不同步/stable才同步)   (okf_validate/对账/核验/清洗)   (机械骨架+LLM提炼,≤50/批)
```

- **本地 = 唯一权威源**（`library/`）；云文档 = 展示/协作层。draft 不上云，stable 才同步。
- **选择性采集**：只采"需要的博主 + 指定/挑选的素材"，不主动全量遍历；未得到的原数据本轮不碰。
- **跨阶段严格串行**；同阶段多素材切片可并行（受各平台风控上限约束）。
- **独立审查**：审查/评估 Agent 与生产 Agent 上下文隔离，只读不改，问题写清单由流水线 Agent 修。

---

## 1. 全链路总览（阶段 × 输入/输出/产物路径）

| 阶段 | 输入 | 动作 | 输出（产物路径） | 决策门 |
|---|---|---|---|---|
| **S0 预判 / 任务定义** | 用户一句需求（博主/链接/主题/素材） | 判形态×素材类型×行业×路线×是否需 OCR/分析/评论×范围 | 任务卡（manifest） | **G0** |
| **S1 采集** | 任务卡 | 按平台/素材类型分路下载 + 字幕 + 评论（选择性） | `library/01_video/`、`02_audio/`、`07_books/`、`08_sources/` 原始文件 | G1/G2 |
| **S2 内容提取** | 原始文件 | 字幕清洗 / FunASR 转写 / 抽帧+OCR / PDF 文本 / 图文 OCR | `transcript.md`、ocr 文本、关键帧、pdf 文本/JSON、图文元数据 | 覆盖率/空稿判定 |
| **S3 多媒体分析** | 转写后复核 | 判型命中 → 画面层+音频层双轨，按行业插件取维度 | 分析报告（路由 video-studio / OKF MethodNote） | **G3** |
| **S4 文稿分型 + 批量 OKF 化** | 全部中间物 | 判目的地（VideoNote/ArticleNote/BookNote/CourseNote/MethodNote）→ 机械骨架 + LLM 提炼（≤50/批） | `library/05_knowledge/<域>/concepts/<类型>/` | **G4/G5** |
| **S5 质检门** | OKF bundle | okf_validate + fused_into 对账 + 五维核验 + G7 清洗门 | 质检报告；draft→stable | **G5/G7** |
| **S6 云文档同步** | stable 页 | 转人读格式 → 串行导入 → 补层 README/索引 | 云 docx URL + 登记 | **G6** |
| **S7 审查迭代** | 已发布产物 | 独立 Agent 复审覆盖/忠实/准确；残留/过时维护 | 审查清单 + 修订任务 | 持续 |

> **目录落点约定**（本地权威源）：
> - 视频转写：`library/05_knowledge/jewelry/珠宝学者郭颖/transcripts/<标题>/transcript.md`（郭颖形态①）
> - 原子知识：`library/05_knowledge/<域>/concepts/{videos,articles,books,courses,topics,reports,methods}/`
> - 评论原始导出：`library/08_sources/{douyin,bilibili}_comments/{id}_comments.json`
> - 采集层文章：`library/06_articles/<域>/<公众号或博主>/`
> - 备份/过程件：`workspace/<本轮批次目录>/`（先备份后修改）

---

## 2. 角色分工（职责边界 × 可用工具集）

| 角色 | 职责边界 | 可用工具 / 真实路径 |
|---|---|---|
| **编排 Organizer** | 接需求、拆任务卡、调度各角色、验收整合、登记 CHANGELOG/TASK_STATUS/索引；**不亲自生产内容** | 本 SOP 任务卡模板；`scripts/doc_health_check.py`；云索引 |
| **采集 Collector** | 按任务卡平台分路下载、字幕、评论；守风控纪律；不越权全量采 | 技能 `~/Doubao/skills/multiplatform-media-fetch/`；`collect_douyin_comments.py`、`collect_bilibili_comments.py`；`platforms/douyin/scripts/generate_excel.py` |
| **提取 Extractor** | 一律把原始素材转"标准中间物"，不直接成文 | `scripts/process/funasr_transcribe.py`（`--lang auto`，日语 `--lang ja`）；`scripts/process/macos_vision_ocr_pipeline.py`；`scripts/process/opencv_keyframe_extractor.py`；`.skills/pdf` 的 `extract_pdf_text.py`（`--structured`）；byted-mediakit-audio/image；单图兜底 `processing/ocr/ocr_vision <图>` |
| **知识化 Knowledge Builder** | 中间物 → OKF 原子页；G5 归并；frontmatter；不复制全文 | `scripts/wrap_wechat_articles.py`（机械骨架，幂等）；okf-wiki 规范；类型词表见 `知识化总规划 §1.2` |
| **质检 QC** | 机械门全跑 + 对账 + 五维核验 + 状态流转判定；只对负责 | `~/Doubao/skills/okf-wiki/scripts/okf_validate.py`；`scripts/fused_into_reconcile.py`；`scripts/frontmatter_consistency_check.py`；`scripts/doc_health_check.py` |
| **云同步 Cloud Publisher** | stable 页 → 人读格式 → 串行导入 → 补 README/索引；不删不移既有云文件 | `lark-cli drive +import/+list`；`lark-cli docs +fetch/+update` |
| **审查 Reviewer（独立）** | 对成品做五维复查，**只读**；问题写清单，不改库 | `docs/workflow/evaluation-agent-template.md`；与生产 Agent 隔离上下文 |

> **红线**：采集不碰登录/支付/验证码（移交人工）；知识化不抄他库正文、不复制全文；质检不替生产 Agent 改内容；云同步不删除/移动/新建空间（除非用户确认）。

---

## 3. 标准任务卡模板（组织者直接复制派发）

> 每阶段只写自己负责的列，下游只读已完成列。命名：`批次-序号`。

### 3.1 任务卡通用头
```yaml
task_id: P7-<批次>-<序号>
目标形态: 读者文稿 | 知识文稿 | 运营文稿 | 视频创作 | 视频分析 | 评论研究 | 双写
素材类型: video | audio | pdf | image | text | 图文（可多选）
行业: jewelry | stock | video_creation | <新>
平台/来源: 抖音|B站|小红书|视频号|YouTube|腾讯VOD|公众号|本地文件|网页
范围: 单条 | 批量 | 增量（选择性：只采指定/挑选的，不全量遍历）
路线预判: subtitle | audio | video-for-ocr | pdf-extract | image-ocr | direct-text | 图文解析
需OCR: 是|否     需视频分析: 是|否（判型依据：___）     需评论: 是|否
跨模态归并目标: <已有 topic 或 新建>
状态: 待办
```

### 3.2 各角色任务卡（一页一张）

**① 采集卡**
- 输入：任务卡（平台+指定素材清单）
- 输出：原始文件落 `library/` + 评论 JSON + 清单更新
- 校验门：数量对账（已采清单 = 指定清单）；风控纪律（抖音 ≥30s/条、单会话 ≤15 条；小红书评论 ≤3 页；B站必直连）
- 交接物：`manifest.csv` 状态列
- 红线：不越权全量遍历；撞登录/验证码/风控硬阻断 → 挂起移交人工，不硬攻

**② 提取卡**
- 输入：原始文件
- 输出：标准中间物（transcript.md / ocr 文本 / pdf JSON / 图文元数据）
- 校验门：覆盖率（每个已下载素材都有中间物）；空稿判定（字数与时长相称，中文约 250–320 字/分钟）
- 交接物：中间物路径写回 manifest
- 红线：单图勿跑视频抽帧流水线（用 `ocr_vision`）

**③ 知识化卡**
- 输入：标准中间物
- 输出：OKF 原子页（frontmatter + 编译摘要 1-3 句 + 3-5 要点 + 来源指针）
- 校验门：`okf_validate` 该批 E=0；逐批不动正文（机械骨架字节断言）；fused_into 双向对账
- 交接物：原子页路径 + fused_into 指针
- 红线：不复制全文；并入已有 topic 为主，确属新主题才新建；跨博主不互抄

**④ 质检卡**
- 输入：一批 OKF 页
- 输出：质检结论（通过/回退）+ 状态流转建议
- 校验门：`okf_validate` E=0、零新增 W60/I11/W80；fused_into 闭合；五维核验（§5.3）
- 交接物：stable/draft 判定 + verified 记录
- 红线：不凭空补 verified；效果数据缺失就标〔待核〕，不编造

**⑤ 云同步卡**
- 输入：stable 页
- 输出：云 docx URL + README/索引登记
- 校验门：串行导入；README 补条目；不删不移既有云文件
- 交接物：云 URL 写回 workspace 维护记录
- 红线：draft 不上云；原始 YAML frontmatter 不裸奔（转人读信息块）

**⑥ 审查卡（独立只读）**
- 输入：待复查文件列表 + 采集层原件 + 对账结论
- 输出：阻塞问题 / 待改进 / 待核 / 已通过 四段清单
- 校验门：五维（evaluation-agent-template §1）
- 交接物：给组织者的登记建议（不直接改库）
- 红线：只读；发现问题登记，修改由流水线执行

---

## 4. 决策门 G0–G7（触发规则 × 判定 × 状态流转）

| 门 | 何时触发 | 判定标准 | 不通过怎么办 |
|---|---|---|---|
| **G0 采集前预判** | 接需求第一步 | 形态/素材类型/行业/路线/OCR/分析/评论/范围八项有依据；**选择性采集**（只采指定素材，不全量） | 缺信息 → 问用户，不猜 |
| **G1 字幕选路** | 平台字幕探测后 | 有字幕→只下字幕；无→最小音频；无音轨→可 OCR 视频(≤720p) | 按六条默认行为（见 workflow-main §5） |
| **G2 OCR 决策** | 预判+兜底 | 需画面文字（图表/界面/实物细节）或兜底（无声/新片静音 -91dB）→ 跑 OCR+抽帧 | 有声优先回音频路线 |
| **G3 多媒体分析** | 转写后复核 | "只看字幕/音频能否还原 80% 价值？" 不能 → 双轨分析 | 能还原 → 跳过，转知识化 |
| **G4 成文分型** | 全部中间物就位 | 按用途选 VideoNote/ArticleNote/BookNote/CourseNote/MethodNote；双写则同 route 指针互连 | 用途不明 → 问用户目的地 |
| **G5 知识化归并 + 升级核验** | 新原子页完成 | 并入已有为主；升 stable 硬门 = **≥2 独立来源 + 逐条结论挂脚注 + 五维核验过** | 单源/证据不足 → 留 draft + `single_source_risk: true` + 文中标「单源待核」 |
| **G6 发布决策** | 产物过质检门 | **仅 stable 才上云**；draft 留本地；放置模块先读内容再归类；补层 README/00_索引 | 残留/过时 → 按 §8.2 处置，不直接删 |
| **G7 清洗门** | 课程/转写稿知识化前 | 拍板选 A：直接 OKF 化、ASR 初稿标 `clean: false`+`draft`；深度清洗并入质检 | 不阻塞主链路；按实况标注，不假设已清洗 |

### 4.1 状态流转（draft → stable）与信任三级

| 状态 | 含义 | frontmatter 写法 | 校验器 I10 显示 |
|---|---|---|---|
| `status: draft` | 机器初稿，未核 | 无 `verified` | unverified（正常） |
| `status: stable` + `verified: ai:doubao` | **AI 已逐条溯源核验**（本轮 P7 干跑新增档） | `verified: { by: "ai:doubao", at: "<ISO8601+08:00>" }` | machine-confirmed |
| `status: stable` + `verified: human:<id>` | 人工核验过 | `verified: { by: "human:<id>", at: "<ISO8601+08:00>" }` | human-reviewed |

> **⚠️ 干跑实测的关键坑（必须照写）**：okf-wiki 校验器是"宽容解析"，它**只识别行内 map `{by:..., at:...}` 或块列表 `- by: ...`**；如果你写成缩进块（`verified:` 下面缩进两行 `by:/at:`），解析器会**静默丢弃该字段**，文档仍显示 unverified 且不报错。**写 verified 一律用行内 map 单行**。

### 4.2 verified / stale_after 规则（引用 `verified-stale-rule.md`）

- `verified` 只在有真实核验处写：AI 核验用 `by: "ai:doubao"`，人工用 `by: "human:<id>"`；机器初稿不写。
- `stale_after` 只给时效内容（行情/点位/价格/粉丝数）；常青科普/方法论（如 MethodNote）**不写**。
- 实质改正文后，旧 verified 不自动延续，需重新核验。
- 拿不准 → 保留原样并标「待核」，不硬改。

---

## 5. 批量执行参数（硬纪律）

1. **≤50/批**：书籍/课程/文章批量 OKF 化按时间倒序分批，每批 ≤50；每批后跑 `okf_validate` E=0 + 数量对账，任一批失败即停、修复后继续。
2. **两段式**：阶段一机械幂等脚本只加 frontmatter 不动正文（逐篇字节断言）；阶段二 LLM 提炼摘要，**不复制全文**（原文只在 `07_books/`/`04_transcript/` 存一份）。
3. **E0 门**：每批后 `python3 ~/Doubao/skills/okf-wiki/scripts/okf_validate.py <bundle目录>` 必须 E=0，零新增 W60（野脚注）/I11（source 未挂脚注）/W80/W81（孤儿）。
4. **对账双向**：采集层 `fused_into` 指针 ↔ 知识层 sources 反指，跑 `scripts/fused_into_reconcile.py`，闭合数 = 应收敛数。
5. **选择性采集**：只采指定/挑选的素材，不主动全量遍历；未得到的原数据本轮不碰。
6. **串行导入云**：同一文件夹并发 `drive +import` 会冲突（错误码 232140101/233523001），必须串行，失败等几秒重试最多 3 次。

---

## 6. 错误回退 / 待核挂起 / 人工介入点

| 情形 | 处置 |
|---|---|
| rate-limit / 临时网络抖动 | **自动重试**（最多 3 次，每次间隔几秒）；云导入撞并发错误码即转串行 |
| 路径找不到 / frontmatter 解析错 / 参数错 | 先怀疑自己（端点/ID/路径/最近改动），不怪凭证；两次失败换通道（换脚本/换目录） |
| 缺独立来源 / 证据不足 / 效果数据未采集 | **标「待核」挂起**，留 `draft` + `single_source_risk: true`，不硬升 stable、不凑数 |
| 登录 / 验证码 / 人工开窗（微信视频号）/ 支付 | **必须人工**，暂停移交控制权，不自动过 |
| 未知日期 / published: unknown-date / 效果数据（粉丝量、互动率、播放数未采集） | **人工/外部**，如实标〔待核〕，**禁止编造**（MethodNote 效果论证只用已采 JSON meta + 模式频次） |
| 云文档删除 / 迁移 / 新建空间 / 毕业 | **必须用户确认**，只提议不擅自执行 |

> **备份与回滚约定**：任何 frontmatter/正文修改前，先把原文件复制到 `workspace/<本轮批次>/backup/`；写操作"只增不删、改动前记录原始值→新值"；发现改错可从 backup 回滚。本 P7 轮备份在 `workspace/P7_orchestration_dryrun_20261013/backup/`。

---

## 7. 新博主 / 新素材冷启动清单（G0 → 首批 stable 上云）

1. **G0 预判**：确认目标形态、素材类型、行业、路线、是否需 OCR/分析/评论、范围（选择性）；生成任务卡。
2. **资产盘点**：列已得素材清单（不主动新采）；建该博主目录与 `manifest.csv` 状态机。
3. **采集落点**：按素材类型落 `library/{01_video,02_audio,07_books,08_sources}/<域>/<博主>/`。
4. **提取**：跑对应提取脚本，产出标准中间物，回写 manifest。
5. **知识化**：先查已有 topics 索引，并入为主；确属新主题才新建原子页；frontmatter 按对应类型规范（BookNote/CourseNote/VideoNote/ArticleNote/MethodNote）。
6. **质检**：`okf_validate` E=0 + 对账 + 五维核验；≥2 独立源才升 stable。
7. **云同步**：stable 页转人读格式 → 串行导入对应云文件夹 → 补层 README 与 00_索引 → 记录云 URL。

> **命名**：原子页文件名 = 稳定 id（BV 号 / article_id / method 英文 slug）；云文档名沿用 `方法笔记M{N}-{标题}（{博主}）` 这类人读名。

---

## 8. 云同步要点（G6 细节）

1. 本地过质检门 → 守则决策树判落点（云盘孵化 or Wiki；Wiki 须用户同意）。
2. **raw YAML frontmatter 不裸奔**：上云前把 frontmatter 转成"状态/归因/类型/证据"人读信息块（见本 SOP 附录模板），正文保留。
3. `lark-cli drive +import --file <人读.md> --type docx --folder-token <token> --name "<人读标题>"`，**串行**。
4. 导入后补层 README（`docs +fetch` 重读 → `docs +update` 局部改）；注意 `block_replace` 后旧 block-id 失效，**再编辑前必须重新 fetch 拿新 id**。
5. 权威源：本地为准；云文档向本地对齐，不反向。

---

## 附录 A. 上云人读信息块模板（替代裸 YAML）

```markdown
# <标题>
> **状态**：stable（ai:doubao / human:<id> 已核验 · 日期）
> **归因**：<博主>
> **类型**：<content_type>
> **证据**：N 个独立来源
---
> 一句话定义
## 模式 / 步骤 / 案例 / 为什么有效（待核处标注）/ 边界
```

## 附录 B. 本 P7 干跑记录（M3/M5 升级核验，2026-10-13）

- **核验对象**：`concepts/methods/pitfall-topic-from-hot-take.md`（M3）、`skit-opening-n-step-structure.md`（M5）。
- **核验方式**：逐句对来源（转写全文 + B 站评论 JSON），五维（事实准确/来源可溯/正文一致/覆盖/待核处置）+ ≥2 独立源。
- **结论**：两页均通过（各 3 独立源、跨博主、脚注↔sources 闭合、无编造）→ 真实升 `stable`，记 `verified: { by: "ai:doubao", at: "2026-10-13T16:30:00+08:00" }`。
- **校验器**：methods bundle 改前 E0·W0·I4 → 改后 E0·W0·I4（M3/M5 由 unverified 转 machine-confirmed，零新增 W60/I11/W80）。
- **发现并回写本 SOP 的缺口**：
  1. **verified 块格式坑**（§4.1）：缩进块被校验器静默丢弃，必须行内 map——已写入 §4.1 警示框。
  2. **效果数据 source 应指本地 JSON**：M5 的 effect 数字（view/like/reply）来自 `08_sources/.../BV1kK4y1w7UN_comments.json`，但其 source `resource` 只写了 B 站 URL，本地不可复算——后续写"带效果数字"的 source，`resource` 优先指本地 JSON。
  3. **block_replace 后 id 失效**（§8.4）：云文档 README 编辑链中需重新 fetch——已写入 §8。

---

*本 SOP 随每次干跑/新批次回写修正；发现规则盲区按"问题驱动更新"立即补进对应章节。*
