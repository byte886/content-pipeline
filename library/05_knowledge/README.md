# 知识成品层（library/05_knowledge）

> **文档类型**：知识层总入口（index）
> **作用**：告诉你这里有哪些行业知识、各自加工到什么程度、从哪进
> **组织规范**：新增知识源前先读 [../../docs/guides/knowledge-source-organization.md](../../docs/guides/knowledge-source-organization.md)

这里是 content-pipeline 五条流水线（采集 → 转写/OCR → 知识成品 → 监控 → 运营）中的**知识成品层**：把下载转写好的原始视频/图文，沉淀成可检索、可复用、可引用的结构化知识。

存储分工（仓库根 `AGENTS.md` §3）：原始音视频在 `library/01_video/`、逐字转写在 `library/04_transcript/` 与各源 `transcripts/`、**清洗后的知识成品才放本目录并入 git**；视频/表格/原始件本地持有不入 git。

---

## 一、两种知识成品形态

本库的知识成品按**加工深度**分两种形态，可并存于同一行业：

| 形态 | 位置约定 | 是什么 | 成熟度标志 |
|---|---|---|---|
| **① 博主综合文档库** | `<行业>/<博主>/` | 把同一博主大量视频按品类**人工归并**成的少数几篇主题长文档（一篇覆盖一个品类/专题），配台账与原始转写 | 主题文档即成品，可读可引用 |
| **② OKF 原子知识库** | `<行业>/concepts/` | 每条视频/图文一篇 OKF 原子笔记（VideoNote/ArticleNote…），再由 `topics/` 跨篇提炼主题融合页 | frontmatter `status: draft → stable`；主题页是第二步语义加工 |

> 形态②遵循 OKF v0.2（技能 `okf-wiki`）：原子笔记批量生成、主题页逐步提炼；形态①是"已经完成跨篇归并"的高密度成品。同一行业两者互补：综合文档给体系，原子笔记给出处与广度。

## 二、行业知识源导航

### jewelry（珠宝·鉴藏）—— 当前主战场

| 知识源 | 形态 | 规模与状态 | 入口 |
|---|---|---|---|
| 珠宝学者郭颖（抖音） | ① 综合文档库 | 192 视频转写 → **17 篇综合知识文档**（14 品类 + 3 潘家园实战）+ 6 早期文档；已完成跨篇归并 | [jewelry/珠宝学者郭颖/README.md](jewelry/珠宝学者郭颖/README.md) |
| 宝石学家老许（B站） | ② OKF 原子库 | **744 篇 VideoNote**（723 draft / 20 stable）+ 10 篇 topics 主题页（占位待提炼）+ 1 篇创业情报 ReportNote | [jewelry/concepts/index.md](jewelry/concepts/index.md) |

行业总入口：[jewelry/README.md](jewelry/README.md)

### stock（股票·行情）

| 知识源 | 形态 | 规模与状态 | 入口 |
|---|---|---|---|
| 财经短视频/直播提取 | 原料态（结构化 JSON） | 336 条（313 短视频 + 23 直播）的行情观点结构化提取 + 情绪/板块汇总；**尚未沉淀为 OKF 成品**（concepts 空） | [stock/README.md](stock/README.md) |
| 股票书籍精华 | 书籍笔记 | 4 本经典精华 + 11 篇 extracted，位于 `library/07_books/stock/` | [../07_books/stock/精华/README.md](../07_books/stock/精华/README.md) |

> 行业切入优先级：当前以**珠宝、翡翠/玉石**为重点（见各运营仓）；股票库为早期试验，暂不扩。

## 三、怎么找到想要的知识

- **要体系化结论**（如"珍珠怎么分级"）→ 先查博主综合文档（郭颖 17 篇）。
- **要某条视频的原话/出处/更全品类广度** → 查 OKF 原子笔记（老许 744 篇，按 category 或 topics 导航）。
- **要珠宝生意/创业/产业带情报** → 老许 `concepts/reports/community-scys-jewelry-business.md`。
- **要历史行情观点/板块统计** → stock `extracted/` 的两个 summary JSON。
- **要核对原始转写** → 各源 `transcripts/` 或 `library/04_transcript/`。

## 四、可信度约定（全层通用）

- 自动转写初稿（`status: draft`）含同音错字与口误，**数字/专名正式引用前必须回看原片**。
- 文档中以 **〔转写〕**（转写存疑）、**〔观点〕**（博主主观看法）、**待补**（未展开/缺来源）显式标注；不编造数字与来源。
- OKF 笔记的可信度以 frontmatter `sources / status / verified / stale_after` 为准，读取时现判，不写死主观分数。

## 五、新增知识源（给 AI 的硬要求）

新增一个博主/行业知识源时，**必须**按 [知识源组织 SOP](../../docs/guides/knowledge-source-organization.md) 建入口文件、选对形态、标好状态、过校验，并在本页"行业知识源导航"登记；不得把成品散落在无入口、无台账、无状态说明的目录里。
