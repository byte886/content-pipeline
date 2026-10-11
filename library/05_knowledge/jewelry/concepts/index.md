# 宝石学家老许 · OKF 原子知识库（concepts）

> **来源**：B站 @宝石学家老许（mid 1841256325）口播视频
> **形态**：OKF v0.2 知识包（bundle）——每条视频一篇原子笔记 VideoNote，跨篇主题在 `topics/` 二次提炼
> **生成**：FunASR 本地转写 → 技能 `okf-wiki` 批量成稿（2026-09-12）
> **行业入口**：[../README.md](../README.md)　**主题索引**：[topics/index.md](topics/index.md)

---

## 一、规模与成熟度（现状如实说明）

| 内容 | 数量 | 状态 |
|---|---|---|
| `videos/` 原子视频笔记 VideoNote | **744** | **723 draft / 20 stable** |
| `topics/` 横向主题融合页 | 10（+ 本 index） | **全部 draft 占位**，待第二步语义加工 |
| `reports/` 报告笔记 ReportNote | 1 | 珠宝创业情报（外部社区综合，已成型） |

**关键认知**：744 篇 VideoNote 绝大多数是 **`status: draft` 的自动转写初稿，未人工校对，含同音错字、口误与未展开数字**。它们的价值是"可检索的出处与广度"，**不能直接当作权威结论照抄**；正式引用前必须：① 打开 frontmatter `sources` 里的 B站原片或本地转写核对；② 优先参考 `stable` 篇与郭颖综合文档的交叉结论。

`topics/` 的 10 个主题页目前是**规划空壳**（"待从多篇 VideoNote 归纳稳定结论并挂来源脚注"），尚无可读结论，不要误当成已沉淀知识。

## 二、目录结构

```
concepts/
├── index.md            ← 本入口
├── videos/             ← 744 篇 VideoNote，文件名 = B站 BV 号
├── topics/             ← 10 篇横向主题（draft 占位）+ index.md
└── reports/            ← 1 篇 ReportNote（珠宝创业情报）
```

- VideoNote 文件名即 B站 BV 号（如 `BV1Cg4y1u7CG.md`），frontmatter 含 `bvid / duration / published / play / words / category / sources / status`。
- `sources` 同时给 B站链接与本地转写稿相对路径（`../../../../04_transcript/<category>/<标题> [BV号]/transcript.md`）。

## 三、744 篇 VideoNote 分类导航（按 frontmatter category 现算）

**主线系列（编号类目）**

| category | 篇数 | 内容方向 |
|---|---|---|
| 02_彩色宝石 | 245 | 红蓝宝、祖母绿、碧玺、尖晶、帕拉伊巴等（最大类） |
| 05_金属首饰与佩戴 | 87 | 金属材质、镶嵌、佩戴搭配、原创成品 |
| 01_钻石 | 58 | 钻石 4C、证书、选钻 |
| 08_行业与商业 | 53 | 行业、定制生意、供应链 |
| 04_有机宝石 | 41 | 珍珠、琥珀、珊瑚等 |
| 07_行情与选购 | 34 | 价格逻辑、进店选购、保值变现 |
| 06_鉴定与避坑 | 23 | 合成/优化/套证/二手鉴别 |
| 11_其他 | 18 | 杂项 |
| 09_品牌新品与动态 | 14 | 品牌、新品、市场动态 |
| 10_珠宝文化与故事 | 6 | 生辰石、历史文化、客订故事 |
| 03_玉石 | 6 | 翡翠、和田玉等 |

**合集系列**

| 合集 | 篇数 | | 合集 | 篇数 |
|---|---|---|---|---|
| 彩宝选购合集 | 44 | | 生辰石合集 | 14 |
| 原创设计首饰 | 37 | | 客订开箱合集 | 9 |
| 钻石购买攻略合集 | 20 | | 黄金彩宝首饰 | 8 |
| 老许的创业系列 | 7 | | 宝石推荐 | 7 |
| 钻石贵/便宜区别 | 6 | | 宝石之国 | 4 |
| 珠宝开箱 | 2 | | | |

> 上表有 category 标签的合计 743 篇，余 1 篇未分类；数字随采集变动，以 frontmatter 现算为准。

## 四、横向主题（topics，待提炼）

[topics/index.md](topics/index.md) 列了 10 个规划主题：钻石选购与4C、彩色宝石图谱与价值、玉石、有机宝石、镶嵌工艺与佩戴、鉴定与避坑、行情价格与选购话术、行业与商业、品牌与新品动态、珠宝文化与故事。

**第二步语义加工的标准动作**（未来精修时）：在某主题下聚合多篇 VideoNote → 归纳稳定结论、逐点挂来源脚注（BV 号）→ 回填该主题覆盖的 VideoNote 链接 → 校验后把 `status` 由 draft 升 stable。可参照郭颖同品类综合文档的成稿深度，但须独立挂老许自己的来源。

## 五、已成型的报告

- [reports/community-scys-jewelry-business.md](reports/community-scys-jewelry-business.md)：**珠宝创业情报**——基于生财有术社区 548→174 篇珠宝帖清洗综合：七条底层规律、14 类经营赛道、五大平台、九大产业带、9 个真实案例、0-1 打法、风险趋势。补科普之外的"怎么做生意"维度。

## 六、怎么用 / 怎么校验

- **按品类查**：在上表定位 category → 到 `04_transcript/<category>/` 或 `videos/` 按 BV 号找笔记。
- **按主题查**：读 `topics/`（注意多为占位）。
- **机械自检**：`python3 ~/Doubao/skills/okf-wiki/scripts/okf_validate.py library/05_knowledge/jewelry/concepts`（E 必修、W 确认）。
- 与郭颖库的分工与品类对照见 [../README.md](../README.md)。
