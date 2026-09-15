# 任务状态台账（TASK_STATUS）

> **文档类型**：Status（状态台账，动态更新）
> **更新频率**：每个子任务完成时、遇到阻塞时
> **维护者**：AI自动维护
> **读者**：AI代理和用户

> **本页是"当前做什么、到哪"的唯一进度真相**，实时更新。
> 需求溯源看 `docs/REQUIREMENTS.md`，开放缺陷看 `project-management/active/ISSUES.md`。
> 稳定技术结论的权威版在 ADR / 工程记忆，本页只放指针、不复制结论。
> 易变计数（已下多少、已转写多少）以现场成品文件为准，不抄进本页。

---

## 依赖与并行前沿

- **阶段① 资源采集**：已完成（313短视频 + 23直播回放 + 277篇文章）
- **阶段② 内容处理**：短视频转写✅、图文OCR✅、直播回放转写⏳（进行中/待启动）
- **阶段③ 知识提取**：工具已开发，待批量运行
- **阶段④ 知识库组织**：方案已设计，待执行
- **项目治理**：文档架构重构✅、证书路径修复✅、_workspace设计✅、WORKFLOW/REQUIREMENTS✅

可并行：直播回放转写（后台运行）与知识提取工具优化可同时进行。

---

## 工单清单（状态：todo / doing / blocked / done）

| 编号 | 标题 | 类型 | 前置 | 状态 | 验收 / 落点 |
|------|------|------|------|------|------------|
| T-01 | 视频号短视频采集 | feature | 无 | **done** | 313个短视频，`data/videos/短视频/` |
| T-02 | 视频号直播回放采集 | feature | 无 | **done** | 23个直播回放，`data/videos/直播回放/` |
| T-03 | 公众号文章采集 | feature | 无 | **done** | 277篇文章，`knowledge-base/02-公众号文章/` |
| T-04 | 短视频转文字 | feature | T-01 | **done** | 313个转写稿，`data/transcripts/短视频/` |
| T-05 | 直播回放转文字 | feature | T-02 | **todo** | 23个转写稿，`data/transcripts/直播回放/`（每个1-3小时，转写时间更长） |
| T-06 | 公众号图片OCR | feature | T-03 | **done** | 910张图片OCR，更新236篇文章 |
| T-07 | 知识提取工具开发 | feature | T-04/T-06 | **done** | `tools/knowledge-extraction/extract_knowledge.py` |
| T-08 | 知识提取批量运行 | feature | T-07 | **todo** | 313个短视频 + 277篇文章的知识提取 |
| T-09 | 高质量URL研究 | research | 无 | **done** | xWT111比默认大69%，`docs/高质量URL研究.md` |
| T-10 | 视频号API研究（方案B） | research | 无 | **todo** | 证书路径已修复，可重新测试 |
| T-11 | 项目治理与文档架构 | refactor | 无 | **done** | DOCUMENTATION_MAP、DIRECTORY_STRUCTURE、ADR、工程记忆、WORKFLOW、REQUIREMENTS |
| T-12 | 捕获工具证书路径修复 | bugfix | 无 | **done** | 改为相对于可执行文件的路径，已验证 |
| T-13 | _workspace运行时工作区设计 | refactor | 无 | **done** | logs/tmp/capture(manifest,state)，`data/_workspace/README.md` |
| T-14 | 知识库汇总生成 | feature | T-08 | **todo** | 按主题组织的知识库汇总 |
| T-15 | 增量采集机制完善 | feature | T-01/T-02/T-03 | **todo** | URL清单对比，只采集新内容 |
| T-16 | 百度网盘同步 | feature | 无 | **todo** | 股票知识库应用，`scripts/netdisk/sync_stock.sh` |
| T-17 | 书籍精华提取 | feature | T-03 | **todo** | 文章中推荐的书籍 → 查找内容 → 形成文稿 |

---

## 关键口径（指针，不展开）

- **视频解密原理**：DecodeKey → ISAAC64生成128KB数组 → XOR文件前128KB → 见工程记忆 `workflow-video-capture`
- **高质量URL参数**：X-snsvideoflag=xWT111（最大3.92MB）→ 见 `docs/高质量URL研究.md`
- **证书与代理方案**：相对于可执行文件的路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall，9.7x实时 → 见 `tools/transcription/`
- **OCR工具**：macOS Vision编译二进制，1.5秒/张 → 见 `tools/ocr/`
- **存储分工**：GitHub(代码+文档) / 本地(视频+转写稿) / U盘(备份) / 百度网盘(镜像) → 见 ADR-001

---

## 下一步（按优先级）

1. **启动直播回放转写**（T-05，后台运行，耗时较长）
2. **测试方案B（视频号API）**（T-10，证书路径已修复）
3. **批量运行知识提取**（T-08，可与转写并行）
4. **完善增量采集机制**（T-15）

---

*最后更新：2026-09-15*
