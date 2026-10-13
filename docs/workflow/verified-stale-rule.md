# verified / stale_after 回填规则与已回填清单（K4 质检·任务三）

> **文档类型**：Reference（规范 + 台账）
> **配套**：校验器 `~/Doubao/skills/okf-wiki/scripts/okf_validate.py`；对账脚本 `scripts/fused_into_reconcile.py`、`scripts/frontmatter_consistency_check.py`。
> **核心原则**：只在有真实人工/来源核验处标 `verified`；`stale_after` 只给明确时效性内容；吃不准的保留原样并标"待核"；写操作只增不删、改动前记录原始值。

---

## 1. 字段语义（与 OKF 校验器口径一致）

| 字段 | 含义 | 何时写 |
|------|------|--------|
| `verified: { by: "human:<id>", at: <ISO8601+08:00> }` | 人工核验过 | **仅有真实人工/来源核验记录时**。机器生成一律不写。 |
| `stale_after: <ISO8601+08:00>` | 内容时效性截止/复审日 | 行情、点位、价格、活动、粉丝数等会随时间变化的内容。常青科普/工具书不写。 |
| `status` | 成熟度 | 机器摘要未人工核 = `draft`；人工核验过 = `stable`。 |

> 校验器联动：`verified.by` 误写 `human/xxx` → W40；`stale_after` 非 ISO8601 → W31；已过期 → W32；无 verified → I10（unverified，正常，不是错误）。

---

## 2. 回填规则（分对象）

### ① 老许 topics（`library/05_knowledge/jewelry/concepts/topics/*.md`，10 页）
- 现状：10 页均已有 `verified: { by: "human:doubao", at: <ISO8601+08:00> }` + `status: stable` + `stale_after`。
- 动作：**保留并核对一致性**。结论：10/10 格式一致（均 human:doubao、均带 +08:00 偏移、均 status:stable）。
  - 时效差异：`品牌与新品动态` stale_after=2027-04-11（6 个月，品牌/上新/成交强时效）；其余 9 页 =2027-10-11（1 年）。该差异为既有人工决策，**本轮不改写**，仅登记。
- 本轮变更：无（只核对）。

### ② 顶底之王 ArticleNote（`library/05_knowledge/stock/concepts/articles/*.md`，278 页）
- 现状：278 页均 `status: draft`，无 verified、无 stale_after；content_type = market_view(269) + howto(9，实际为暴跌/大涨应对、午评、支撑位等行情评论)。
- 规则：行情/点位类原子页为强时效市场评论，**只补 stale_after，不补 verified**（机器摘要未人工核）。
- 取值：统一 `stale_after: 2027-01-01T23:59:59+08:00`（未来复审日；不触发 W31/W32）。依据：2020–2021 历史点位评论已无实时参考价值，统一打复审旗标，正文自带 published 日期。
- 动作：**278/278 已回填**（脚本 `scripts/backfill_stale_after_dingdi.py`，幂等）。
- 原始值 → 新值：`(无 stale_after)` → `stale_after: 2027-01-01T23:59:59+08:00`（插在 `status: draft` 行后，只增不删）。

### ③ 郭颖 23 篇（`library/05_knowledge/jewelry/珠宝学者郭颖/*知识文档.md`）
- 现状：23 篇均 `type: Knowledge / status: stable`，无 verified、无 stale_after。
- 规则：**不凭空加 verified**（无人工核验记录）；**不滥加 stale_after**（主体为常青宝玉石科普/潘家园方法论，非实时行情报价）。
- 动作：本轮**不改任何郭颖文件**。其中价格/选购角度较强的 3 篇（`南红手串选购`、`翡翠组配用料溢价`、`黄金贵金属`）登记为**待核**——后续若确认含具体成交价/行情，再补 stale_after。

### ④ 其余 draft（stock 书籍 BookNote、courses 等）
- 规则：一律**不加 verified**。无明确时效的工具书草稿保持 draft。
- 动作：本轮不改。

---

## 3. 已回填清单（原始值 → 新值）

| 对象 | 文件数 | 字段 | 原始值 | 新值 | 依据 |
|------|--------|------|--------|------|------|
| 顶底之王 ArticleNote | 278 | stale_after | （无） | `2027-01-01T23:59:59+08:00` | A股行情/点位强时效，统一复审旗标 |
| 顶底之王 ArticleNote | 278 | verified | （无） | 不补 | 机器摘要未人工核 |
| 老许 topics | 10 | verified/stale_after | 已有 human:doubao | 保留不改 | 核对一致 |
| 郭颖 23 篇 | 23 | verified | （无） | 不补 | 无人工核验记录 |
| 郭颖 23 篇 | 23 | stale_after | （无） | 不补（3 篇待核） | 常青科普；价格类待确认 |

---

## 4. 待核项（交人工/下一轮）

1. 郭颖 `南红手串选购`、`翡翠组配用料溢价`、`黄金贵金属` 是否含具体成交行情 → 决定是否补 stale_after。
2. 老许 `行情价格与选购话术` 当前 stale_after=1 年，是否应与 `品牌与新品动态` 一样收紧到 6 个月（既有决策，本轮不动，登记）。
3. 顶底之王 278 页 `published: unknown-date` 的若干篇，日期待补（不影响 stale_after 合法性）。

---

## 5. 校验器联动结论（回填后）

- stock concepts：E=0，W60=0，I11=0；I10=302（unverified，正常）、I12=11。新增 stale_after 未引入 W31/W32。
- 全程未引入新 W60/I11。

---

*本规则随后续轮次复用；新增对象类别时先在 §2 补规则再回填。*
