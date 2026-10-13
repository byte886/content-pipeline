# 评估 Agent 复查模板（evaluation-agent-template）

> **文档类型**：Reference（参考资料 — 可复用 SOP 模板）
> **用途**：K4 质检收尾与后续轮次中，供「评估 Agent」对一批知识成品（BookNote / VideoNote / ArticleNote / Concept / ReportNote）做独立复查。
> **原则**：只复查、不重写；发现问题登记到清单，修改由流水线 Agent 执行。事实必须可溯源，不凭空补数字。
> **配套校验器**：`~/Doubao/skills/okf-wiki/scripts/okf_validate.py`（硬错误 E 必须 0；W60/I11 为本轮重点关注项，不得新增）。

---

## 0. 复查输入清单（评估 Agent 开工前先收齐）

| 输入 | 说明 |
|------|------|
| 待复查文件列表 | 相对仓库根的 .md 路径（按目录批量：books/videos/articles/topics/reports） |
| 采集层原件 | `library/06_articles/**/meta.json|article.json`、`library/04_transcript/**`、`library/07_books/**/extracted/` |
| 对账脚本结论 | `scripts/fused_into_reconcile.py`、`scripts/frontmatter_consistency_check.py` 的最新跑批输出 |
| 本轮变更记录 | 谁改了哪些 frontmatter（verified/stale_after 回填、合并标注），原始值→新值 |

> 红线：评估 Agent **只读**；发现问题写进输出清单，不直接改库。

---

## 1. 五维复查清单（逐项过，可打勾）

### 维度 A · 事实准确性
- [ ] 正文里的数字、日期、人名、点位、价格能否在采集层原件 / 来源页找到对应？
- [ ] 行情/点位/成交价类内容是否标注了"口播/发布时点"，而非当作现状？
- [ ] 有没有 AI 编造的、原件里根本不存在的句子（对照编译摘要逐句抽查 ≥20%）？
- [ ] 作者/机构名、书名、版本号与来源页一致，无张冠李戴。

### 维度 B · 来源可溯（sources ↔ 正文脚注）
- [ ] frontmatter `sources[].id` 每个都在正文以脚注（`[^id]` 或定义行）出现。
- [ ] 正文每个脚注 `[^id]` 都能在 sources 里找到同 id 背书（无野脚注 = 无 W60）。
- [ ] 采集层 `fused_into` 指针与知识层反指双向闭合（跑 `fused_into_reconcile.py`）。
- [ ] source 的 `resource` 路径真实存在（本地路径无死链；URL 标注采集日期）。

### 维度 C · 正文一致性（frontmatter ↔ 正文）
- [ ] frontmatter 声称的来源数与正文实际引用的来源数对得上（跑 `frontmatter_consistency_check.py`）。
- [ ] `description` 与正文摘要语义一致，不夸大、不偏题。
- [ ] `tags` 能在正文主题里找到依据，无乱贴标签。
- [ ] `status` 与内容成熟度匹配：机器摘要未人工核 → `draft`；人工核验过 → `stable`。

### 维度 D · 覆盖完整性
- [ ] 聚合页（Concept/topics）声称覆盖 N 个来源，正文脚注是否真的引用了这 N 个？
- [ ] 同一主题有没有漏收的采集件（对照 manifest / 采集层目录数）？
- [ ] 重复件（同源双源，如 pdf/mobi 双提取）是否已判重合并、互指清晰、零删除。
- [ ] index.md 是否登记了该被消费的页面（孤儿页 W81 是否为有意为之）。

### 维度 E · 待核项处置
- [ ] 所有"机器生成待核"内容是否都带了 `draft` 状态或"待核"标注，未被伪装成已核验。
- [ ] `verified` 字段只在真实人工/来源核验处出现（`human:<id>`），无凭空补 `verified`。
- [ ] 时效性内容（行情/价格/活动）是否按规则补了 `stale_after`，且日期合理。
- [ ] 吃不准的条目是否保留原样并标"待核"，而不是硬下结论。

---

## 2. 信任等级与 verified / stale_after 速查（与校验器口径一致）

| 情形 | 处置 |
|------|------|
| 无 verified，内容为机器初稿 | 保持 `status: draft`，信任等级 = unverified（I10，正常） |
| 人工核验过 | 补 `verified: { by: "human:<id>", at: <ISO8601+08:00> }`，信任升 human-reviewed |
| 行情/点位/价格强时效 | 补 `stale_after: <ISO8601+08:00>`，按内容时效取值，标注依据 |
| 无时效的科普/工具书 | 不补 stale_after；不补 verified |
| 拿不准 | 保留原样，清单里标"待核"，不硬改 |

> 严禁：凭空给 draft 加 `verified`；把人工误写成 `human/xxx`（W40）；stale_after 写成非 ISO8601（W31）或已过期未处理（W32）。

---

## 3. 输出格式（评估 Agent 必交）

```
复查批次：<日期 / 轮次>
复查范围：<目录或文件数>
校验器结论：E=<n>（必须0）  W60=<n>  I11=<n>（与基线对比，新增数写清）
对账脚本：fused_into 闭合 <x>/<y>；一致性不一致 <n>

[阻塞问题]（事实错误 / 野脚注 / 断链，必须修）
  1. <文件>：<问题> → <证据原件位置> → <建议动作>

[待改进]（不阻塞，但建议下轮处理）
  1. <文件>：<问题>

[待核项]（评估 Agent 也拿不准，登记交人工）
  1. <文件>：<疑点>

[已通过]（抽查无问题的维度，简述）

[给组织者的登记建议]
  - CHANGELOG 一句话条目
  - 是否需要回写 TASK_STATUS / DOCUMENTATION_MAP（评估 Agent 不直接改，只建议）
```

---

## 4. 基线对照（K4 本轮起点）

- fused_into 双向指针：298/298 闭合（老许 20 + 顶底之王 278）。
- frontmatter↔正文：0 野脚注 / 0 空锚；ArticleNote、ReportNote 的采集背书 source 不做行内引用属设计约定。
- 校验器：E=0；W60=0；I11 基线 = jewelry 2 条（ReportNote 的 src-source/src-manifest）、stock 0 条。后续轮次以「不新增」为合格线。

---

*本模板随 K4 收尾与后续轮次复用；发现新的复查盲区就补进 §1 对应维度。*
