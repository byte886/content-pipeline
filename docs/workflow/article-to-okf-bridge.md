# 文稿 ↔ 知识库融合桥（ArticleNote → OKF）· P3 方案

> **文档类型**：Process / SOP（P3 先行评估交付版）
> **日期**：2026-10-12 ｜ **状态**：方案先行版（设计 + 试点 2 条已跑通 E0W0）；正式批量执行待 3 项拍板（见文末）
> **底座**：OKF v0.2（技能 `okf-wiki`）｜ 关联：郭颖形态①（`type: Knowledge` 长文档）、老许形态②（`type: VideoNote` 原子笔记 + topics）
> **一句话**：把已经躺在 `library/06_articles/` 的文章 / 图文，按既有 ArticleNote 形态接进 OKF 知识库，与 VideoNote 在 topics 层跨模态归并——**不复制正文、不新建空壳、并入为主**。
> 来源：本项目现状盘点 + 技能 okf-wiki 规范；不确定项标「待核」。

---

## 0. 现状盘点（修正早前认知）

| 维度 | 事实 | 出处 |
|---|---|---|
| 总量 | 06_articles 共 **298 篇 .md**：jewelry/老许 **20** + stock/顶底之王 **278**（其中 manifest type=article 277 + 1 条 None） | `library/06_articles/` 实盘 |
| 老许 20 篇 | **已是 `type: ArticleNote`、`status: draft`**，每篇一目录（`article.md` + `images/` + `ocr/` + `meta.json`）；sources 用 `src-bili`(opus URL) + `src-ocr`；`generated.by: doubao/m2-article-harvest` | 老许 `article.md` frontmatter |
| 老许来源 | 全是 **B站图文动态**（bilibili_dynamic / opus，DYNAMIC_TYPE_DRAW），`content_type` 如 `goods_price` | 老许 `manifest.json` |
| 顶底之王 277 篇 | **纯公众号文章**（wechat_official），每篇目录 `article.html` + `article.json` + `content.md` + `images/`；**`content.md` 无 frontmatter、纯正文** | 顶底之王 `content.md` 首行 |
| 与知识库关系 | `05_knowledge/jewelry/concepts/` 中**无任何对 06_articles 的引用**——20 篇老许 ArticleNote 是**孤儿**，与 744 篇 VideoNote + 11 topics 完全断链 | 全库 grep |
| 早前缺口修正 | "0 ArticleNote" 的说法**不准确**：ArticleNote 形态**已存在于采集层**，真正缺口是**它没有被桥接进知识层、也没有和 VideoNote 跨模态归并** | 本盘点 |

**结论**：不缺"ArticleNote 格式"，缺的是"桥"——把采集层 ArticleNote 接进知识层、并与视频原子笔记在 topics 合并的**成文规则与链接协议**。

---

## 1. ArticleNote 形态定稿建议（frontmatter 规范）

沿用老许已跑通的 20 篇 + 试点，统一如下（标准档 draft 起步）：

```yaml
---
type: ArticleNote                 # 固定值（design doc 词表已有）
title: "<文章标题>"
description: "<一句话摘要 + 来源平台/日期/图数 + draft 待核>"
tags: [<博主>, <行业>, <主题>, <来源平台>]
domain: jewelry | stock | general
content_type: goods_price | market_view | howto | story | ...   # 沿用采集层分类
sources:
  - id: src-<模态>                 # 见 §3 src 标签协议
    kind: <模态枚举>               # 新增：显式标注来源模态
    resource: "<原文 URL 或本地采集层相对路径>"
    title: "<原文标题>"
    author: "human:<博主id>"
    last_modified: <ISO8601+08:00>
generated: { by: "doubao/<采集器>", at: <ISO8601+08:00> }
status: draft                     # 自动稿一律 draft；人工精修才升 stable
published: <发布时刻 ISO8601>      # 文章发布时间（区别于 generated.at）
article_id: "<平台+日期+id>"       # 稳定 ID，防重
# —— 采集层自定义键（消费方不得报错）——
n_images: 9
ocr_chars: 295
---
```

**与既有先例对齐点**：`type/status/generated/sources.id` 完全复用老许 20 篇与 design doc；新增 `kind:`（模态显式标注）是本桥的唯一增量，用于跨模态归并时机读区分来源。

---

## 2. manifest 链接协议（route / artifact 指针互连）

问题：采集层（06_articles）与知识层（05_knowledge）目前互不认识。建议**双向指针，不复制正文**：

| 方向 | 指针位置 | 写法 | 作用 |
|---|---|---|---|
| 采集层 → 知识层 | 06_articles 每篇 `meta.json` 增 `fused_into` 字段 | `fused_into: "library/05_knowledge/jewelry/concepts/topics/<主题>.md"` 或 `null` | 标记这篇文章已被哪个 topic 吸收，防重复归并 |
| 知识层 → 采集层 | topic / ArticleNote 的 `sources[].resource` | 指向采集层原文相对路径 + 原文 URL | 逐句可回源 |
| 台账对账 | 沿用 `xlsx_to_manifest.py` 思路 | 知识层 ArticleNote 数 = 采集层 `has_content=true` 且 `fused_into≠null` 数 | 数量闭合，零遗漏 |

> 关键纪律：**正文只在采集层存一份**；知识层 ArticleNote 是"编译后摘要 + sources 指针"，不是把原文再抄一遍。跨模态归并到 topic 时，topic 用 `[^<article_id>]` 脚注指回采集层。

---

## 3. 跨模态归并规则（src 标签协议）

同一主题的**视频 / 音频 / PDF / 图文 / 公众号**合并进同一知识条目（topic 或综合文档），来源分别标注：

| src id 前缀 | kind 枚举 | 来源模态 | resource 示例 |
|---|---|---|---|
| `src-douyin` | douyin_video | 抖音视频转写 | `https://www.douyin.com/video/<vid>` |
| `src-bili-video` | bili_video | B站视频转写 | `https://www.bilibili.com/video/<BV>` |
| `src-bili-opus` | bili_opus | B站图文动态 | `https://www.bilibili.com/opus/<id>` |
| `src-wechat` | wechat_article | 公众号文章 | `mp.weixin.qq.com/s?...` |
| `src-xhs` | xhs_note | 小红书笔记 | `xhslink.com/...` |
| `src-pdf` | pdf_book | 书籍/PDF | `07_books/<域>/raw/...pdf` |
| `src-audio` | audio | 音频/播客 | `02_audio/...` |
| `src-transcript` | local_transcript | 本地转写稿 | `04_transcript/.../transcript.md` |
| `src-ocr` | local_ocr | 本地 OCR 稿 | `06_articles/.../ocr/` |

**归并动作**：topic 页的 `sources[]` 按上表把同一主题的不同模态并列挂出；正文关键结论用 `[^src-xxx]` 脚注标注出自哪种模态。**来源冲突按权威度裁决**：官方/原片 ＞ 多源互证 ＞ 高赞观点 ＞ 单一博主说法。

---

## 4. 增量归并原则（并入为主、新建为例外）

1. **新文章/图文进来，先查 topic 索引**：已有同主题 topic → 把本篇作为新 `src-*` 条目并入该 topic（补 sources、补一节、更新 description 聚合数）；确无同主题才新建 ArticleNote 原子页。
2. **ArticleNote 是原子层，topic 是融合层**：文章先落成 draft ArticleNote（原子、可检索），再由 topic 跨篇提炼——与 VideoNote→topics 的两步走完全对称。
3. **同主题跨模态合并**：一篇讲"祖母绿价格"的公众号文章，与讲祖母绿的 VideoNote，最终进**同一个 topics 主题页**，不各建一页。
4. **实质改正文后旧 verified 不延续**；价格/行情类 ArticleNote 必须设 `stale_after`（一年），文化/货盘类可放宽。
5. **不复制他库正文**：老许图文只写老许增量，不抄郭颖综合稿。

---

## 5. 与郭颖①/老许②双形态的关系（结论）

**结论：ArticleNote 是"原子知识层"的一种类型，与 VideoNote 并列，归入形态②（concepts bundle 家族），不是郭颖形态① 的变体。**

| 形态 | 本质 | 粒度 | 承载内容 |
|---|---|---|---|
| ① 郭颖综合库 `type: Knowledge` | 人工跨篇归并的**长文档**（一品类一篇） | 粗 | 已成体系的高密度结论 |
| ② 老许 concepts `type: VideoNote` | **逐条原子笔记** + topics 融合 | 细 | 每条视频一篇 draft，再提炼 topic |
| **ArticleNote（本桥）** | **逐条原子笔记**（文章/图文） | 细 | 每篇文章一篇 draft，**与 VideoNote 一起喂 topics** |

**理由**：文章/图文是"单篇单来源"的原料，与"单条视频单来源"的 VideoNote **同粒度、同生命周期（draft→stable→topic）**，天然并列；郭颖形态①是"已经跨篇归并完"的成品层，文章原料不该直接塞进那种长文档（破坏其"一品类一篇、人工归并"结构）。因此桥的落点是：**在 concepts bundle 里加 `articles/` 子目录（与 `videos/` 平级）放 ArticleNote**，`topics/` 页同时引用 `videos/` 与 `articles/`。郭颖① 不动。

---

## 6. 试点验证（已跑通，E0W0）

试点 bundle（非生产、独立 workspace，未污染 content-pipeline）：`…/agents/s_000EtBINsLW/artifacts/article-to-okf-pilot/`

| 试点 | 来源 | frontmatter 要点 |
|---|---|---|
| `stock-beishijijin-2021-07-22.md` | 顶底之王公众号文章（原本无 frontmatter） | `type: ArticleNote`、`src-wechat` + `src-local-html`、`status: draft`、4 类背离框架归并 |
| `laoxu-opus-wulvmu-2021-12-03.md` | 老许 B站图文（原已 ArticleNote 草稿） | `src-bili-opus` + `src-local-ocr`、`goods_price`、跨模态归并提示 |

校验结果：`okf_validate.py` → **E0 · W0 · I6，退出码 0**（6 条 I = draft 未核 unverified + source id 未挂脚注，均为预期信息项，不阻塞）。

---

## 7. 落地步骤与交付门

**落地两步（P3 批量执行轮 2026-10-13 已完成）**：
1. ✅ **老许 20 篇**：按实际珠宝主题（读 OCR 正文判定，description 为模板话术不可用）归入 **5 个既有 topic**（品牌与新品动态 10 / 行情价格与选购话术 6 / 行业与商业 2 / 镶嵌工艺与佩戴 1 / 彩色宝石图谱与价值 1，**未新建 topic**）；5 个 topic 页追加 sources 条目 + `[^opus-*]` 脚注（脚注↔sources 对账一致，无 W60）；20 篇 meta.json 全部回填 `fused_into`（20/20）。10 篇 image_only 品类待核（OCR 无有效字，按货盘展示归入，人工看片后可能微调）。
2. ✅ **顶底之王 278 篇批量 wrap**：wrapper `scripts/wrap_wechat_articles.py` 按时间倒序 6 批（50/50/50/50/50/28）只加头不动正文（逐篇字节断言），278/278 frontmatter 可解析；`article_278`（原 type=None、有内容）按同规则 wrap；4 条 unknown-date 存量条目按同规则处理（`published: unknown-date`）；两线并行提炼 **278 原子页**（`05_knowledge/stock/concepts/articles/`，正文=编译摘要 1-3 句 + 3-5 要点 + 来源指针），采集层 article.json 回填 `fused_into` 278/278。

**交付门**：`okf_validate E0` + `doc_health_check 0 ERROR` + 数量对账（`fused_into` 数 = topic 引用数）。
**✅ 已达成（2026-10-13）**：stock bundle E0·W0·I278（index 已登记 278 原子页）、jewelry bundle E0（W721 为存量孤儿页非本次引入）、`doc_health_check` 0 ERROR、fused_into 对账 **298/298 闭合**（顶底之王 278 + 老许 20）。

---

## 主理人拍板（2026-10-12 已决，三项全部通过）

- [x] **顶底之王 277 篇批量 wrap**：同意，但**分批执行**（≤50 篇/批，按时间倒序；先建 `05_knowledge/stock/concepts/` 最小骨架：articles/ + topics/ + index.md）。每批只加 frontmatter 不动正文、`status: draft`、description 标注"机器生成待核"、批内 `okf_validate E0` 校验 + 数量对账（wrap 数 = manifest type=article 数）。任一批评验失败即停、修复后继续。**本轮仅定稿设计，批量执行另起一轮。**
- [x] **`articles/` 子目录落点**：认可 `05_knowledge/<域>/concepts/articles/`（与 videos/ 平级）。理由：ArticleNote 与 VideoNote 同粒度（单篇单来源原子笔记）同生命周期（draft→stable→topic），并列最对称；topics 融合层不变，同时引用 videos/ 与 articles/。jewelry 域已建目录（本轮落地），stock 域随 wrap 建。
- [x] **`kind:` 新键接受**：OKF v0.2 允许自定义 key（消费方不得因未知字段报错）；试点 E0W0 已验证。**老许 20 篇已批量回填**（src-bili→`bili_opus`、src-ocr→`local_ocr`，逐篇插入 sources 条目，正文不动），校验 0 硬错误。
