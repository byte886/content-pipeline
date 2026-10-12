# 内容工作流主流程（WORKFLOW-MAIN：S0–S7 + 决策门 G0–G6）

> **文档类型**：Process（流程规范 — 工作流详设）
> **日期**：2026-10-12 ｜ **状态**：P1 骨架已落地（含多模态扩展）；各批 SOP 按规划文档 §10 继续补充
> **读者**：AI 代理（执行任何采集→知识化→云文档任务前必读）
> **与 docs/WORKFLOW.md 关系**：本文件 = **详设**（阶段 / 决策门 / 路由 / 衔接载体）；WORKFLOW.md = **概览 + 校验门**（只放链接，不重复细节）。
> **与规划文档关系**：缺口、待办、风险、分阶段计划见 `视频知识工作流-融合规划-2026-10-12.md`（下称"规划文档"）；本文件只放可执行设计，**有冲突以规划文档待办登记为准**。

---

## 0. 定位与阅读顺序

执行任务前按序读：
1. 规划文档 §1（执行摘要）→ §4（目标工作流）→ §10/§11（当前批次与待办）
2. 本文件（当前阶段与决策门详设）
3. `../WORKFLOW.md`（概览与校验门）
4. 对应技能 / 守则（`~/Doubao/skills/multiplatform-media-fetch/`、`~/Doubao/skills/okf-wiki/`、`.skills/pdf`、飞书守则）

---

## 1. 阶段总览（S0–S7）

```
S0 任务定义与预判(采集前) ──G0──> S1 采集(多模态下载+评论+字幕) ──G1/G2──> S2 内容提取(转写/OCR/PDF/图文)
      │                                                                      │
      │G0: 目标形态×素材类型×行业×路线                                          └──G3──> S3 视频/多媒体分析(按行业)
      v                                                                                 │
S7 云文档发布与维护 <──G6── S6 质检与迭代 <──G5── S5 知识化(OKF,跨模态归并) <──G4── S4 最终文稿合成
      (残留/过时/毕业/索引)   (机械门+人工复核+评估Agent)  (归并/新建)     (多源融合成文)
```

| 阶段 | 目标 | 核心产物 | 校验门 | 详设 |
|---|---|---|---|---|
| S0 任务定义与预判 | 生成任务卡（形态 × 素材类型 × 行业 × 路线） | 任务卡（manifest） | G0 字段齐、决策有依据 | §3 |
| S1 采集 | 多模态采集 + 评论 + 字幕 | mp4 / m4a / pdf / webp / txt + 评论导出 | 数量对账、文件可读、风控纪律 | §4 |
| S2 内容提取 | 产出一律转标准中间物 | transcript.md / ocr 文本 / pdf 文本 / 图文元数据 | 覆盖率、空稿判定、翻译完成 | §5 |
| S3 视频/多媒体分析 | 判型命中 → 按行业双轨分析 | 分析报告（路由 video-studio / OKF） | 判型命中、路由正确 | §6 |
| S4 最终文稿 | 多源融合按角色成文 | 最终文稿（06_articles） | 字数与时长相称、来源可溯 | §7 |
| S5 知识化（OKF） | 文稿/素材 → 知识条目，G5 归并 | OKF bundle 更新 | okf_validate E0W0、对账零遗漏 | §8 |
| S6 质检与迭代 | 机械门 + 人工复核 + 评估 Agent | 质检报告 + 修订 | 全部门过、评估通过 | §9 |
| S7 云文档发布维护 | 按守则发布 + 残留/过时/重复维护 | 云文档更新 + 维护记录 | 00_索引已补、对账无残留 | §10 |

---

## 2. 决策门速查（G0–G6）

| 门 | 名称 | 输入 | 规则（来源） | 输出 | 状态记录 |
|---|---|---|---|---|---|
| **G0** | 采集前预判 | 用户需求（博主 / 链接 / 主题 / 行业 / 素材） | ① 目标形态（文稿 / 知识库 / 视频分析 / 评论研究 / 双写组合）；② 行业 → domain-plugin；③ 路线预判（字幕 / 音频 / OCR / PDF 解析 / 图文解析）；④ 视频分析判型；⑤ 评论需要；⑥ 范围；⑦ **素材类型分路**（§3.2）；⑧ 跨模态归并预判 | 任务卡 | manifest.status |
| **G1** | 字幕探测后选路 | 平台字幕探测 | SKILL.md 六条默认行为：字幕优先 → 最小音频 → 可 OCR 视频（≤720p） | route = subtitle / audio / video-for-ocr | fetch-manifest.route |
| **G2** | OCR 决策 | 预判 + 兜底 | 预判画面文字（图表 / 界面 / 实物细节）或兜底（实际无声 / 新片静音流） | 是否跑 OCR + 抽帧 | fetch-manifest.ocr |
| **G3** | 多媒体分析决策 | G0 预判 + 转写后复核 | 判型表（§6.1）；行业插件需要 | 分析报告 + 路由（video-studio / OKF） | manifest.analysis |
| **G4** | 成文决策 | 全部中间物 | 读者文稿 / 知识条目 / **双写**（同一躯干出两产物，同 route 指针互连，规划文档 §6.2） | article / knowledge / 双产物 | manifest.article_path / knowledge_path |
| **G5** | 知识化归并 | 新条目 + 现有 OKF | 并入已有为主，新主题才新建；**跨模态同主题合并**（规划文档 §6.2-5、§6.3）；补采来源进 frontmatter | OKF bundle 更新 | manifest.knowledge_status |
| **G6** | 发布决策 | 质检通过产物 | 云文档决策树（守则·二）；放置模块；补 00_索引；**生成视频 / 发表前必须过全部检查门**（token 前置） | 云文档更新 + 索引 | manifest.cloud_status |

---

## 3. S0 任务定义与预判（G0 详设）

### 3.1 任务卡字段（manifest 状态机，扩展自郭颖 manifest.csv 16 列）

| 字段 | 取值 / 说明 |
|---|---|
| task_id | 任务编号（批次-序号） |
| 目标形态 | 读者文稿 / 知识文稿 / 运营文稿 / 视频创作文稿 / 视频分析 / 评论研究 / 双写（多选；用途分型见 §7.1） |
| 素材类型 | video / audio / pdf / image / text / 图文（多选） |
| 行业 | 珠宝 / 视频创作 / 股票 / 其他 → domain-plugin 名 |
| 平台 / 来源 | 抖音 / B站 / 小红书 / 微信视频号 / YouTube / 腾讯VOD / 公众号 / 本地文件 / 网页 |
| 范围 | 单条 / 批量 / 全量 / 增量 |
| 路线预判 | subtitle / audio / video-for-ocr / pdf-extract / image-ocr / direct-text / 图文解析 |
| 视频分析 | 需要 / 不需要 + 判型依据 |
| 评论 | 需要 / 不需要 |
| 跨模态归并 | 归并目标主题（如有） |
| 状态 | 待办 → 采集中 → 提取中 → 分析中 → 成文中 → 知识化中 → 质检中 → 已发布 |

### 3.2 G0 素材类型分路矩阵

| 素材类型 | 采集路由 | 提取路由 | 中间物 | 参考（规划文档） |
|---|---|---|---|---|
| video | §4.1 平台策略 | §5.1 视频提取 | transcript / ocr / 关键帧 | §5.1–§5.3 |
| audio | §4.2 音频采集 | FunASR 转写（语音边界 / 人声分离用 byted-mediakit-audio） | transcript.md | §5.4 |
| pdf | §4.3 PDF 采集 | extract_pdf_text.py（`--structured` JSON）；版面重要渲染 PNG；扫描件 OCR | pdf 文本 / JSON / PNG | §5.4 |
| image | §4.4 图片采集 | image-ocr / macos_vision_ocr_pipeline + 元数据探测 | OCR 文本 + 元数据 | §5.4 |
| text / 网页 | 公众号采集 SOP / article-pipeline | 直接取文 / 清洗 | 文章文本 | §5.4 |
| 线上图文 | xiaohongshu note | 逐张 OCR / 视觉理解 + 元数据入库 | webp 集 + 元数据 + 评论 | §5.4 |

**决策原则**：先问"这条素材的**内容价值载体**是什么"——口播观点 → 转写；画面文字 → OCR；版面/表格 → PDF 结构化提取；实物/视觉 → 图片分析 + 行业插件；再按 §3.2 选路由。

---

## 4. S1 采集（多模态路由 + 评论）

### 4.1 视频平台策略速查（详情见技能 references/platforms/** 与规划文档 §5.1）

| 平台 | 采集方式 | 登录 / 风控 |
|---|---|---|
| YouTube | yt-dlp + 代理（被拦 `--browser chrome`） | 必走代理 |
| B 站 | yt-dlp 下 BV；UP 列表登录页 fetch | **必直连**（代理→412），限速 2MiB/s |
| 抖音 | 匿名 ttwid → Chrome → 浏览器直读三级回退；currentSrc + `__vid` 铁证法 | 直连；静默风控；收藏遍历 ≥30s/条、单会话 ≤15 条 |
| 小红书 | Playwright 直读 DOM 专用脚本（note / comments / user / search） | 扫码持久化；三道门；禁深爬评论 ≤3 页 |
| 腾讯 VOD | CDP 取参 → AES 解密 | 复用已开 Chrome；人工点播放 |
| 微信视频号 | MITM 捕获 → 人工开窗一步 → Isaac64 解密 | 必电脑微信登录 + 人工一步 |

### 4.2 音频采集

- 入口：本地音频文件 / 播客 RSS / 录音。先用 `byted-mediakit-audio`（probe-audio-metadata 探测、detect-voice-activity 定位语音、separate-voice 人声分离），再 `funasr_transcribe.py` 转写。
- 产物：`library/02_audio/<行业>/<主题>/` + transcript.md。

### 4.3 PDF 采集

- 入口：.skills/pdf（extract_pdf_text.py 提取文本 / `--structured` 出 JSON；版面重要时渲染 PNG 复查；扫描件走 OCR）。电子资料批量转码另见 `../guides/books-extraction.md`。
- 产物：`library/07_books/` 或按主题归入 `library/08_sources/` + 提取文本。

### 4.4 图片 / 线上图文采集

- 图片：byted-mediakit-image（image-ocr、probe-image-metadata、evaluate-image-quality）+ macos_vision_ocr_pipeline.py。
- 小红书图文：`xiaohongshu_downloader.py note "<带 xsec_token 的笔记 URL>"` → 图文 webp 集 + 元数据 + 评论 JSON。
- 公众号文章：公众号采集 SOP（`../guides/wechat-official-article.md`）。
- 产物：`library/08_sources/` + OCR 文本 + 元数据。

### 4.5 评论采集（矩阵见规划文档 §5.2）

- 抖音：浏览器直读评论列表（低频串行、单会话 ≤15 条）→ `{vid}_comments.json`。
- 小红书：`xiaohongshu_downloader.py comments`（≤3 页风控）→ `{note_id}_comments.json`。
- B 站 / 视频号：正文抽取待 P2 验证；计数入台账。
- 产物归属：`library/08_sources/`；S4 作选题 / FAQ / 验证信号。

### 4.6 S1 校验门

- [ ] 全量清单与主页一致、状态清单已生成
- [ ] 风控纪律合规（抖音 ≥30s/条、≤15 条/会话；小红书评论 ≤3 页）
- [ ] 评论导出字段齐（user / content / like / time，平台适用时）

---

## 5. S2 内容提取（多模态 → 标准中间物）

| 素材 | 提取动作 | 标准中间物 |
|---|---|---|
| 字幕 | clean_subtitle.py 清洗 | clean.txt |
| 音频 / 视频音轨 | funasr_transcribe.py（`--lang auto`，日语 `--lang ja`） | transcript.md |
| 视频画面 | macos_vision_ocr_pipeline.py + opencv_keyframe_extractor.py | ocr 文本 + 关键帧 |
| PDF | extract_pdf_text.py（`--structured`） | pdf 文本 / JSON |
| 图片 | image-ocr / Vision OCR | OCR 文本 + 元数据 |
| 图文 | 逐张 OCR + 元数据 | webp 集 + 文本 + 元数据 |
| 文本 / 网页 | 直接取文 / 清洗 | 文章文本 |

- 翻译：非中文默认译中（贴合中文同类作者口吻，不是硬译）。
- 校验门：转写覆盖率（全部已下载素材都有中间物）、空稿判定（有中间物且字数与素材时长相称，中文约 250–320 字/分钟）、manifest 路由与实际产物一致。

---

## 6. S3 视频 / 多媒体分析（G3）

### 6.1 判型表（来源：技能 references/process/video-effect-analysis.md §一）

核心问题：**只看字幕 / 音频能否还原 80% 价值？** 不能 → 进画面层 + 音频层双轨分析（叙事结构 HOOK→CTA、情绪弧线、镜头语言、可复用提示词）。

### 6.2 行业 × 分析需求矩阵（规划文档 §6.4，P5 扩充插件覆盖多模态）

| 行业 | 画面需求 | 分析侧重 | 产物路由 |
|---|---|---|---|
| 珠宝 / 鉴藏 | 实物细节、种水色地工 | OCR + 特写帧 + 品类维度 | OKF 知识条目 |
| 视频创作 / 生成 | 运镜、结构、情绪、提示词 | 画面层 + 音频层双轨 | video-studio 创作对标 |
| 课程 / 知识 | 板书、图表、论证 | OCR + 章节切稿 | OKF + article |
| 泛口播 / 观点 | 观点、论据 | 转写为主 | article / 知识条目 |

### 6.3 产物路由

- 创作对标类（钩子 / 分镜 / BPM / 提示词）→ **video-studio 创作对标库**（先例：郭颖 B 级首批 10 条工单）。
- 知识条目类（鉴别点 / 方法论）→ OKF **MethodNote**（P5 实现）。
- 校验门：判型有依据、产物路由落点正确、分析报告标注来源视频。

---

## 7. S4 最终文稿合成（G4）

### 7.1 文稿用途分型（G4 先定目的地，G0 目标形态据此选）

同一批素材按**用途/目的地**可产出不同类型文稿，按行业与需求组合（可多选）：

| 文稿类型 | 目的地 | 结构依据 | 落点 |
|---|---|---|---|
| 读者文稿 | 面向读者阅读 | article-pipeline §4 七类作者角色结构 | `library/06_articles/` |
| 知识文稿 | 沉淀鉴藏知识体系 | OKF KnowledgeNote（frontmatter / sources / 分级标注） | `library/05_knowledge/`（经 S5） |
| 运营文稿 | 自媒体发布（标题 / 文案 / 口播稿 / 平台适配） | 运营方法（郭颖研究、平台适配规则） | we-media-ops 发布侧 |
| 视频创作文稿 | 生成视频用（脚本 / 分镜 / 提示词 / 创作对标卡片） | 视频分析方法（画面层+音频层，video-effect-analysis） | video-studio |

> 判断依据：**先问"这份文稿给谁用、达成什么"**——沉淀知识 → 知识文稿；发平台引流 → 运营文稿；驱动视频生产 → 视频创作文稿；给人读 → 读者文稿。行业差异（珠宝 / 视频创作 / 股票…）体现在内容维度与结构侧重，由 domain-plugin 提供。

### 7.2 多源融合清单

字幕 / 转写文本 + OCR 文本 + 评论信号 + 视频分析报告 + PDF 章节 + 图文要点 → 按作者角色（教学 / 新闻评论 / 测评 / 经验分享 / 访谈口播 / 宣传带货…）套结构成文（article-pipeline，权威源 `~/Doubao/skills/multiplatform-media-fetch/references/pipeline/article-pipeline.md`）。

### 7.3 双写决策（G4）

- 目标形态=读者文稿 → 06_articles；
- 目标形态=知识文稿 → 直接 S5；
- 目标形态=运营文稿 / 视频创作文稿 → 对应目的地产出（运营→we-media-ops；视频创作→video-studio，可同时出创作对标卡片）；
- 双写 → 同一躯干出多产物（如知识文稿 + 运营文稿），manifest 同 route 指针互连（融合桥 SOP 见 P3：`article-to-okf-bridge.md`，跨模态归并见规划文档 §6.2-5）。

### 7.4 S4 校验门

- [ ] 字数与时长相称（引用转写源核对）
- [ ] 每条关键观点可回溯来源（视频 / PDF / 图文 URL）
- [ ] 评论信号有据（引用评论条目或明确未使用）
- [ ] 文稿类型与目的地一致（§7.1 分型命中）

---

## 8. S5 知识化（OKF，G5）

### 8.1 规范与形态

- 规范：okf-wiki（bundle = index / log / PROJECT-AGENTS / concepts / references；唯一硬必填 `type`；E1/E2/E3 与 W10–W81 判定见 okf_validate.py）。
- 形态：Knowledge（郭颖，23 篇）/ VideoNote（老许，744 篇 draft）/ ArticleNote（P3 定稿）/ MethodNote（P5 实现）。

### 8.2 归并规则（G5）

1. **并入已有知识文档为主**，确属新主题才新建（郭颖：145 科普 → 14 品类、46 实战 → 3 手册）。
2. **跨模态同主题合并**：视频条目 + 音频精华 + PDF 章节 + 图文要点 + 文章观点 → 同一知识文档；来源分别标注（`src-douyin` / `src-pdf` / `src-xhs` / `src-article`）。
3. **补采来源必须进 frontmatter sources**（或对账脚本解析正文附录——待核③，P3/P4 统一）。
4. 跨博主不互相抄（老许只写增量）。

### 8.3 S5 校验门

- [ ] okf_validate.py 无 E（`--strict` 无 W 或按 `--max-warnings`）
- [ ] 吸收对账零遗漏（vid 集合 × sources 集合差集为空）
- [ ] index / log 已同步更新

---

## 9. S6 质检与迭代

### 9.1 检查门（机械门 → 半沉淀 → 缺位，详见规划文档 §7.1）

- ✅ `okf_validate.py` / `doc_health_check.py` / `transcript_dup_scan.py` + `video_visual_dup_scan.py`
- ⚠️ 吸收对账差集（P4 固化脚本）；A/B/C 分级（P4 规则化部分）
- ❌ 语义一致性 / 幻觉自检、frontmatter↔正文一致性、`verified: human:`、`stale_after`（P4 补齐）

### 9.2 闭环与触发

- 触发：交付点（必跑全部机械门）→ 增量后（对账 + 查重）→ 持续复审（每月或重大更新后）。
- 独立评估 Agent：复查覆盖性（全部高价值素材已知识化）、忠实性（观点可回溯）、行业准确性；上下文与生产 Agent 隔离。
- **前置门**：凡后续生成视频 / 发表的内容，必须全门通过才放行（token 前置）。

### 9.3 S6 校验门

- [ ] 机械门 0 ERROR（或记录在案豁免）
- [ ] 评估 Agent 复查结论通过（有记录）
- [ ] 对账零遗漏、无新增近重复

---

## 10. S7 云文档发布与维护（G6）

### 10.1 发布流程

1. 质检通过 → 守则决策树判定落点（云盘孵化 or Wiki，Wiki 须用户同意）；
2. 放置对应项目 / 模块（先读内容再归类、成套不拆散）；
3. **补 00_索引**（守则·四.5）；
4. 记录发布（本地 workspace 维护记录一份）。

### 10.2 维护

- 残留 / 过时 / 重复检测与处理：见规划文档 §8.2（本地权威源对账、退役标注 `[已退役 日期：原因]`、去重、口径旁注）。
- 毕业机制：成型稳定 → 向用户提议迁 Wiki；迁移前必须用户确认；迁移后清空壳并更新总导航与索引（守则·六）。
- 权威源：**本地 = 权威源，云文档 = 展示 / 协作层**；出入以本地 OKF + 原始素材为准。

### 10.3 S7 校验门

- [ ] 00_索引已补链接
- [ ] 对账无残留（本地 ↔ 云盘 ↔ Wiki）
- [ ] 用户确认类操作（删除 / 迁移 / 新建空间 / 毕业）均有确认记录

---

## 11. 衔接载体与多智能体

- 衔接载体 = **任务卡 / manifest 状态机**（§3.1 字段表）：每阶段只写自己负责列，下游只读已完成列。
- 角色分工：编排 / 采集 / 处理 / 分析 / 成文 / 知识化 / 质检 / 评估（独立）/ 云文档，详见规划文档 §9。
- 并行：同阶段多素材切片并行（抖音批次 ≤15、≥30s/条）；跨阶段严格串行。
- 人类介入点：登录 / 验证码 / 人工开窗（视频号）、云文档删除 / 迁移 / 新建空间 / 毕业确认。

---

## 12. 相关文档索引

| 文档 | 用途 |
|---|---|
| `视频知识工作流-融合规划-2026-10-12.md` | 融合规划总文档：现状 / 缺口 / 分阶段计划 / 待办登记（**待办与风险以它为准**） |
| `../WORKFLOW.md` | 项目整体工作流概览（七阶段版）+ 校验门 |
| `../guides/` | 单点操作 SOP（视频号 / 公众号 / 增量 / 转写 / 资产台账 / 知识源组织等） |
| `~/Doubao/skills/multiplatform-media-fetch/` | 采集 / 转写 / OCR / 视频分析子能力（权威源） |
| `~/Doubao/skills/okf-wiki/` | OKF 规范与校验器（权威源） |
| `.skills/pdf`、`.skills/byted-mediakit-audio`、`.skills/byted-mediakit-image` | PDF / 音频 / 图片处理技能（权威源） |
| 飞书《云盘归档与组织规则（AI工作守则）》 | 云文档组织规则（权威源） |

---

*本文档随流程演进持续更新。P2 起各批 SOP 按规划文档 §10 落地后，在本索引补登记。*
