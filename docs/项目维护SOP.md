# 项目维护 SOP

> **文档类型**：Process（项目治理 — 维护与接手）
> **读者**：AI 代理 / 维护者
> **触发**：① 每次准备提交前；② 开新任务窗口 / 上下文变大要交接；③ 不确定"这条信息该写到哪、文档现状是否可信"时。
> 本文件只规定**信息落点、维护节奏、冷启动验收、体检门**；变更分级、存储分工、命名规则已在他处成文，本页只放指针，不复述。

---

## 1. 单一真相源（SSOT）路由表 —— 一条信息只落一处

| 信息类型 | 唯一落点 | 别处只允许 |
|---|---|---|
| 当前做什么、下一步、工单状态、待拍板项 | `project-management/active/TASK_STATUS.md` | 放指针 |
| 已知缺陷 / 阻塞 / 坑 | `project-management/active/ISSUES.md` | 放指针 |
| 一次性专项任务的执行档案 | `project-management/active/<task>.md` | 台账登记一行 |
| 定了不改的架构/方案决策（含否决项） | `project-management/decisions/ADR-NNN-*.md`（只增不改） | 引用 |
| 跨会话稳定的技术结论（编译层） | `project-management/memory/`（index 登记） | 引用 |
| 阶段复盘 / 评审 | `project-management/reviews/` | — |
| **过程日志：聊了什么→结论→为什么、当前纠结** | `docs/HANDOFF.md`（倒序追加） | 结论定稿后编译进 ADR/memory |
| 需求与功能范围 | `docs/REQUIREMENTS.md` | 放指针 |
| 四阶段流水线与校验门 | `docs/WORKFLOW.md` | 放指针 |
| 长期规划 | `docs/ROADMAP.md` | — |
| 平台/场景"怎么做" | `docs/guides/*.md`、`docs/research/*.md` | WORKFLOW 放概览+链接 |
| 目录职责 / 存储分工 / 命名 | `docs/DIRECTORY_STRUCTURE.md` | — |
| 所有文档与脚本的入口索引 | `docs/DOCUMENTATION_MAP.md` | — |
| 易变数字（采集量、下载进度、当天日期） | 台账 / manifest / inventory | 他处**不写死**，只写"以台账为准+口径日期" |

**规则**：易变进度只留在台账；HANDOFF 记过程与理由，定稿结论必须编译进 ADR/memory/SOP，不在 HANDOFF 长期堆结论。新增/移动/删除任何持久文档，必须同步 `docs/DOCUMENTATION_MAP.md`。

---

## 2. 维护节奏

| 时机 | 必做动作 |
|---|---|
| 每完成一个子任务 / 里程碑 | 更新 TASK_STATUS（状态五档中文：待办 / 进行中 / 受阻 / 挂起 / 已完成）；重要决策往 HANDOFF §1 倒序追加一条；定稿结论编译进 ADR/memory |
| 遇到缺陷 / 阻塞 | 登记 ISSUES，给复现与影响；解决后更新，不删号 |
| 准备 `git commit` | 走 §4 提交前检查清单，**体检 0 ERROR 才提交** |
| 用户说"开新窗口 / 换新窗口 / 上下文大了" | 走 `docs/新窗口接手开场白.md`：老窗口收口 → 用户开窗两步 → 新窗口六问验收 |
| 大任务（>3 内容 / >1 小时 / 多工具链）开始 | 按 AGENTS §2.5 建执行状态记录（`workspace/`，不入库） |

---

## 3. 变更影响分级

沿用 `AGENTS.md` §2.3：L0 顺手修复直接做；L1 高扩散（批量重命名/跨目录移动/≥5 处级联/改治理规范本身）先出方案+影响清单、用户确认；L2 架构/流程先讨论。拿不准就高不就低。

写新文档前强制走 `AGENTS.md` §2.4：先 `grep -rn "关键词" docs/ project-management/`，指认现有权威源，已被承担就不新建。

---

## 4. 提交前检查清单

1. 易变进度只在台账，他处无写死的过时数字；HANDOFF 已追加本轮重要决策。
2. 新增/移动文档已在 DOCUMENTATION_MAP 登记；ADR 只增不改；空目录/空章节/0 引用脚本已处理（AGENTS §2.6）。
3. **无凭证/票据/原始素材误入 git**：禁止视频/音频/PDF/逐字稿原文/明文密钥/`exportkey`/`pass_ticket`/`sessionInfo`/`/tmp/capture*`；**`.secrets/` 整个目录不入库（含 `.enc` 加密件），凭证仅本地持有**（见 ADR-003、ISSUE-014）。
4. 跑体检（仓库根），**必须 0 ERROR**（WARN 可记录后提交）：
   ```bash
   python3 scripts/doc_health_check.py
   ```
5. `git status` 复核改动面与本次意图一致；提交信息写清"做了什么、为什么"。

---

## 5. 冷启动验收（六问）

> 新会话**不翻旧聊天**，按 `AGENTS.md` §1.1 的恢复顺序读完，应答出下面六问；答不上、或文档自相矛盾，**先修文档再动手**（说明仓库自描述有缺口）。六问是验收题，答案权威源在右列、不在本页抄死。

| # | 冷启动六问 | 答案权威源 |
|---|---|---|
| ① | 项目是什么？主线 / 当前在采哪些平台与行业源？ | README、`docs/REQUIREMENTS.md`、ADR-004（多平台流水线）、`config/sources.json` |
| ② | 四阶段走到哪、最近完成了什么？ | `docs/WORKFLOW.md`、TASK_STATUS「最近完成」 |
| ③ | 下一步做什么？哪些项等用户拍板？你的推荐？ | TASK_STATUS「下一步」「待拍板」 |
| ④ | 有哪些开放问题 / 已知坑 / 数据缺口？ | ISSUES、各 research 文档的"坑/否决项" |
| ⑤ | 红线是什么？（代理/ClashX、微信风控、存储、去重、参数化、人机边界） | AGENTS §2/§3、采集 SOP 各"硬约束" |
| ⑥ | 关键命令？（捕获启停、下载解密、转写、OCR、体检、git） | 各 SOP「快速参考」、本文 §6 |

---

## 6. 关键命令速查（指针，完整参数见各 SOP）

```bash
# 文档体检（提交前必跑，0 ERROR）
python3 scripts/doc_health_check.py

# 视频号 B方案抓全量（首选，人工刷新一次主页；国内直连 upstream 传空串）
cd platforms/wechat_channels/video-capture
./video-capture -replay-list -short-probe -output /tmp/cap.json -upstream ""
bash stop.sh                          # 停止并自动清系统代理（禁 kill -9 / 禁 kill 全端口）

# 下载解密 / 转写（参数化，知识型默认 min 清晰度）
python3 platforms/wechat_channels/video-downloader/batch_download_v4.py <manifest> <outdir> short|live [start] [min|default|max]
~/.venvs/funasr/bin/python platforms/wechat_channels/video-transcribe/batch_transcribe.py ...
```

---

## 7. 来源边界与诚实性

- 数字、口径、"已验证/可行"必须有来源（实测日志、research 文档、manifest）；推测写"待验证/不确定"，不把一方说法当结论。
- 已否决的死路写进 ADR 或 research 的"否决项"，后续不重复试（如视频号列表走纯 HTTP、反编译/重签微信、faster-whisper 等）。
- 体检保证结构/链接/登记/无泄露；**内容时效仍靠人/台账**，这是体检覆盖不到的部分。
