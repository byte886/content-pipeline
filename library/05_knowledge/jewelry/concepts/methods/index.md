# 方法提炼（concepts/methods）

> 跨博主沉淀的**内容/运营方法论**原子页——回答"博主怎么做内容、怎么做运营、为什么受欢迎"，与"懂什么货"的原料知识（videos/topics/书籍课程文档）分层。
> 规划权威：仓库内 `docs/workflow/方法提炼规划-2026-10-13.md`（容器选型 / 类型词表 / 来源协议 / 提炼流程 S1–S6）。

## 一、容器定位（为什么独立、不喂 topics）

- **读者不同**：topics（如"行情价格与选购话术"）是给消费者买货的领域知识；本目录是给内容生产者/运营者的元方法。
- **粒度不同**：topics = 一个领域主题聚合；本目录 = 一个方法一页原子页，与 videos/ 一视频一页同构。
- **跨域可复用**：方法论未来可向 stock 等其他域迁移；当前先落地 jewelry bundle，反向指针挂回原料页，不改动原料知识。
- **反向链接**：topics 页"关联条目"可引用本目录方法页；本页正文"关联条目"链接回原料 VideoNote / 知识文档。

## 二、类型与 content_type 词表

`type: MethodNote`（OKF v0.2，硬必填仅 type）。`content_type` 取值：

| content_type | 含义 |
|---|---|
| `trust_building` | 信任建立：权威背书、人设、预期管理、失败复盘 |
| `content_strategy` | 内容策略：选题公式、口播结构、记忆点设计 |
| `audience_building` | 涨粉与社群：评论区利用、粉丝参与栏目、争议话题 |
| `monetization` | 变现与导流：线下服务、私域、回收话术 |
| `selection_method` | 选品决策框架的"写法"（具体挑货知识仍留品类文档；本批暂未立页） |

## 三、来源标注协议

| 标签 | 来源 | 用途 |
|---|---|---|
| `src-transcript-*` | 本地转写稿（郭颖 `珠宝学者郭颖/transcripts/<标题>/transcript.md`；老许 `04_transcript/...`） | 口播结构/口诀/情景剧主证据 |
| `src-comments-*` | `08_sources/{douyin,bilibili}_comments/*.json` | 受欢迎信号佐证 |
| `src-douyin-*` / `src-bili-opus-*` | 平台原片 URL（标注采集日期） | 元数据 |
| `src-cloud-research-*` | 云盘研究稿（如《郭颖研究-为什么受欢迎》） | 二手归纳，正文降权标〔研究稿〕 |

**升 stable 硬门**：≥2 个独立来源；逐条结论挂脚注；单源或证据不足留 `status: draft`，不编造、不凑数。效果数据（粉丝量/互动率）未采集，只用已采 JSON meta + 模式频次论证。

## 四、方法页登记

* [authority-plus-grounded-trust](./authority-plus-grounded-trust.md) - ✅ stable：权威身份+接地气双轨信任建立法（trust_building · 郭颖 · 3 源）
* [numbered-formula-topics](./numbered-formula-topics.md) - ✅ stable：数字口诀化选题与韵文记忆点（content_strategy · 郭颖+老许 · 4 源）
* [pitfall-topic-from-hot-take](./pitfall-topic-from-hot-take.md) - 🔵 draft 待核：避坑/争议话题借势选题（audience_building · 郭颖+老许 · 3 源）
* [skit-opening-n-step-structure](./skit-opening-n-step-structure.md) - 🔵 draft 待核：情景剧开场+N步清单口播结构（content_strategy · 郭颖+老许 · 3 源）

## 五、候选登记（证据不足，暂不立页）

* **comment-recruit-offline-service**（暂定 method_id）评论区征集→线下一对一参与式栏目：仅有郭颖潘家园招募转写 + 同源派生《潘家园淘货实战手册》（同一批 14 条视频派生，非独立来源）；无该栏目评论/转化数据。待补招募片评论 JSON、线下成交反馈，≥2 独立源后立 draft 页。

*本 index 为子目录导航页，按 OKF 规范不带 frontmatter（E3 门）。新增/升 stable 页后顺手登记本表。*
