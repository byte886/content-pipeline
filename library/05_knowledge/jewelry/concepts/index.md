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
| `topics/` 横向主题融合页 | 10（+ 本 index） | **10 篇均 stable**（第二步语义加工已完成，合计引用 255 篇次 VideoNote） |
| `reports/` 报告笔记 ReportNote | 1 | 珠宝创业情报（外部社区综合，已成型） |

**关键认知**：744 篇 VideoNote 绝大多数是 **`status: draft` 的自动转写初稿，未人工校对，含同音错字、口误与未展开数字**。它们的价值是"可检索的出处与广度"，**不能直接当作权威结论照抄**；正式引用前必须：① 打开 frontmatter `sources` 里的 B站原片或本地转写核对；② 优先参考 `stable` 篇与郭颖综合文档的交叉结论。

`topics/` 的 10 个主题页已完成第二步语义加工、**全部升 stable**：每篇聚合多篇 VideoNote，Answer-First 归纳可执行结论、逐点挂 BV 来源脚注、文末回填引用的 VideoNote。价格/新品/行情类结论含时效，以各页 `stale_after` 与标注的口播时间为准；与「珠宝学者郭颖」综合文档做了差异化（郭颖强基础体系，老许强原创设计/客订/工艺/商业一手增量）。

## 二、目录结构

```
concepts/
├── index.md            ← 本入口
├── videos/             ← 744 篇 VideoNote，文件名 = B站 BV 号
├── topics/             ← 10 篇横向主题（均 stable）+ index.md
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
| 04_有机宝石 | 41 | 珍珠、沉香、有机材质手串等（库内无琥珀蜜蜡专期） |
| 07_行情与选购 | 34 | 价格逻辑、进店选购、保值变现 |
| 06_鉴定与避坑 | 23 | 合成/优化/套证/二手鉴别 |
| 11_其他 | 18 | 杂项 |
| 09_品牌新品与动态 | 14 | 品牌、新品、市场动态 |
| 10_珠宝文化与故事 | 6 | 生辰石、历史文化、客订故事 |
| 03_玉石 | 6 | 危料翡翠鉴别/行情、金镶玉、黄金镶翡翠 |

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

## 四、横向主题（topics，均 stable）

[topics/index.md](topics/index.md) 的 10 个主题已全部成稿：镶嵌工艺与佩戴、行业与商业、鉴定与避坑、行情价格与选购话术、品牌与新品动态、有机宝石、钻石选购与4C、彩色宝石图谱与价值、珠宝文化与故事、玉石。

**已完成的语义加工动作**：每篇聚合多篇 VideoNote → Answer-First 归纳稳定、可执行结论（鉴别/工艺/材质/价格/避坑尽量表格）→ 逐点挂来源脚注（BV 号 + B站链接）→ 文末回填实际引用的 VideoNote → 校验通过后 `status` 升 stable。与郭颖同品类综合文档差异化：基础体系点到为止、突出老许原创设计/客订/工艺/商业一手增量，不照抄郭颖。个别主题的覆盖缺口（如珠宝文化缺生辰石体系、玉石缺和田玉/南红/绿松石）已在各页内显式标注。

## 五、已成型的报告

- [reports/community-scys-jewelry-business.md](reports/community-scys-jewelry-business.md)：**珠宝创业情报**——基于生财有术社区 548→174 篇珠宝帖清洗综合：七条底层规律、14 类经营赛道、五大平台、九大产业带、9 个真实案例、0-1 打法、风险趋势。补科普之外的"怎么做生意"维度。

## 六、怎么用 / 怎么校验

- **按品类查**：在上表定位 category → 到 `04_transcript/<category>/` 或 `videos/` 按 BV 号找笔记。
- **按主题查**：直接读 `topics/` 下 10 篇 stable 主题页（价格/新品类注意时效标注）。
- **机械自检**：`python3 ~/Doubao/skills/okf-wiki/scripts/okf_validate.py library/05_knowledge/jewelry/concepts`（E 必修、W 确认）。
- 与郭颖库的分工与品类对照见 [../README.md](../README.md)。
