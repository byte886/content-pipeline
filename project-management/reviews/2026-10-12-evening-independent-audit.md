# 全仓旁观者评审报告（2026-10-12 晚间·独立评审）

> **文档类型**：Review（评审报告）
> **评审者**：MainAgent 独立旁观者视角（非治理 Agent 自评）
> **对象**：content-pipeline 全仓（根/ docs/ library/ platforms/ processing/ core/ domains/ scripts/ workspace/ project-management/）
> **前置**：2026-10-12 白天已做过一次全仓评审（治理 Agent），本次为**复核 + 查漏**

## 一、基础结论

白天评审已闭环的部分（复核通过，无需再动）：
- 死链 0（doc_health_check 0 ERROR）；旧脚本 `scripts/fetch_articles.py` 已删；workspace/ 仅 README 入库；ISSUE-018~020 已关闭；domains/jewelry 已写"并入鉴藏总域"过渡说明；ADR-005 已补改名留痕。

## 二、本次新发现问题（6 项）

| # | 级别 | 问题 | 证据 | 建议修正 |
|---|------|------|------|----------|
| A-1 | **P1** | `library/` 缺顶层 README：9606 文件、8 个编号目录（00_manifest/01_video/02_audio/**04_transcript**/05_knowledge/06_articles/07_books/08_sources），**编号跳号（缺 03）无说明、无入口导航** | `ls library/` 无 README；03 无 git 历史 | 补 `library/README.md`：编号体系表 + 03 跳号说明（03 从未启用/预留）+ 各目录一句话 |
| A-2 | **P1** | **TASK_STATUS 进度总览仍是旧四阶段**（资源采集/内容处理/知识提取/知识库组织），与新的七阶段工作流（WORKFLOW.md S0–S7）**不衔接**——导航层与台账层冲突 | TASK_STATUS 头部"当前进度总览"表 vs WORKFLOW.md 七阶段 | 进度总览改为七阶段视角（S0–S7），四阶段内容降为子环节或历史注记 |
| A-3 | **P1** | **AGENTS.md §2.4 未指向新规范** `standards/DOCUMENTATION_PRINCIPLES.md`（文档类型词典/落位决策表/README 防则）——后续 AI 只读 AGENTS 不会知道有新规范，会重犯"正文塞 README" | AGENTS.md §2.4 只指 DOCUMENTATION_MAP + WORKFLOW | AGENTS.md §2.4 加 DOCUMENTATION_PRINCIPLES 指针（必读） |
| A-4 | **P2** | **CHANGELOG 漏登 10-12 晚间 5 个 commit**：9e1799d（云文档组织落地）/ 8a730e8（工作流规划 P1）/ dabc6fa（workflow README 补强）/ c78bc5b（文稿分型入工作流）/ 5281516（文档治理补强） | CHANGELOG 2026-10-12 节止于白天"全仓评审治理"条目 | 补登 5 条（按格式 `［新增/变更/维护］一句话+commit`） |
| A-5 | **P2** | `domains/` 缺总说明：jewelry（已并入 heritage）、stock（旧域）、heritage（新总域 6 子域）三者并存，**stock 去留/关系未说明**；上次评审判"domains/README 无需补"，旁观者视角存疑 | domains/ 下无 README；jewelry/README 写"已归入鉴藏总域"；stock/knowledge_base 仍活跃 | 补 `domains/README.md`（三域关系 + stock 状态说明）；stock 是否归档由用户拍板 |
| A-6 | **P2** | doc_health_check 存量 WARN：`docs/guides/wechat-official-article.md` 含"占位符" | 体检输出 | 核查占位符，补齐或标注待补 |

## 三、观察项（低优先，本次不动）

- O-1：platforms/douyin|bilibili README 101–103 行偏 SOP 化（模块文档可接受，观察是否违反"README 只导航"）。
- O-2：docs/archive/ 内含旧仓名（历史快照，按归档原则不改）。
- O-3：docs/guides/audio-transcription.md 含本机环境细节（.venvs 路径/版本），与技能通用流程分工清晰，可接受。

## 四、修正验收标准（迭代闭环）

1. A-1～A-6 全部处理，每项写明做了什么；
2. `python3 scripts/doc_health_check.py` 0 ERROR（WARN 需说明）；
3. DOCUMENTATION_MAP / project-management/README（如需）同步登记；
4. git 提交推送，工作树干净；
5. CHANGELOG 补登本轮；
6. 修正完成后：基础打牢 → 继续 P2（评论采集 + 多模态素材接入，规划 Agent 原序列）。
