# ADR-005: 仓库二次改名留痕（multiplatform-content-pipeline → content-pipeline）

> **状态**：已采纳（Accepted）
> **日期**：2026-10-12（留痕）；改名实际发生于 2026-10-09
> **决策者**：用户拍板
> **影响范围**：仓库名、GitHub 远端、本地目录、跨仓指针与文档命名

## 背景

- ADR-004（2026-09-15）记录了第一次改名：`stock-knowledge-base → multiplatform-content-pipeline`，确立"多平台采集→内容处理→知识库/文稿/视频生成"的定位与五层架构。
- 第一次改名后，用户反馈 `multiplatform-content-pipeline` 名称过长、且 `multiplatform` 隐含属性已不再需要（体系内其他仓均为 2 词命名风格）。
- 2026-10-09 用户拍板二次改名 `multiplatform-content-pipeline → content-pipeline`，并已执行 GitHub rename + 本地目录 mv + `git remote set-url` + 全链指针同步（含子模块 URL）。
- 此次改名**此前仅在根级 CHANGELOG（2026-10-09）登记，无对应 ADR**。按本仓"ADR 只增不改"原则（见 ADR-004 文末与 project-management/README.md），仓库名属架构级决策，应补 ADR 留痕，而非修改 ADR-004。

## 决策

二次改名为 **`content-pipeline`**，自 2026-10-09 起生效。

理由：

1. **英文标准术语**：`content-pipeline` 准确对应"内容流水线"本质，比 `multiplatform-content-pipeline` 简洁。
2. **砍掉隐含属性**：`multiplatform` 不再写入仓名，多平台能力由架构（platforms/ 插件化）承载，不体现在命名上。
3. **体系命名统一**：与体系内其他仓的 2 词英文命名风格一致。
4. **执行面已完成**：GitHub rename（`github.com/byte886/content-pipeline`，public，master）+ 远端 URL 更新 + 全链指针同步；旧 GitHub URL 自动重定向，不影响 git 操作。

本 ADR 仅作留痕，不回溯改写 ADR-004（第一次改名的历史决策记录保持原样）。

## 后果

### 正面
- 仓名更短、更地道，冷启动路径 `~/Desktop/content-pipeline/` 更清晰。
- 跨仓指针统一指向新名，无双名并存漂移。

### 负面 / 注意
- 历史引用中 `multiplatform-content-pipeline`、`stock-knowledge-base` 作为**历史名**保留在 ADR-004 / archive / CHANGELOG 中属正常；当前态文档（memory concept、README、台账）应统一为 `content-pipeline`。
- 外部若仍引用旧名，依赖 GitHub 自动重定向过渡。

## 参考

- ADR-004《架构重构为多平台内容流水线》（第一次改名 stock-knowledge-base → multiplatform-content-pipeline）
- CHANGELOG 2026-10-09［变更］仓库改名条目
- `git remote -v` = `git@github.com:byte886/content-pipeline.git`

---

*本文档为决策记录，只增不改。后续仓库名/架构调整应新增 ADR，不修改本文档。*
