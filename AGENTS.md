# AGENTS.md — AI代理操作手册

> **文档类型**：Governance（治理规范 — AI操作手册）
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理（每次启动自动加载）

> 本文档是AI代理的操作手册，命令式、可执行。执行任何任务前必须先阅读本文档对应部分。

---

## 1. 执行前必读

### 1.1 冷启动（首次接触 / 开新窗口 / 跨阶段切换）
按序读，不凭文件名猜测、不直接写代码：
0. **跨体系任务先路由**：属业务意图（发什么/定方向）→ 先读运营仓 `~/Desktop/self-media-ops/docs/SYSTEM_STRATEGY.md`；属运行机制/路由疑问 → 先读本仓 `docs/SYSTEM_ARCHITECTURE.md`（本仓=采集底座+体系运行机制层）
1. `README.md` — 项目概览与新会话快速恢复
2. `docs/DOCUMENTATION_MAP.md` — 文档地图（快速入口）
3. `docs/WORKFLOW.md` — 四阶段流水线（判断当前阶段）
4. `docs/HANDOFF.md` — §1 倒序项目日志（聊了什么→结论→为什么）+ §3 当前纠结
5. `project-management/active/TASK_STATUS.md` + `active/ISSUES.md` — 当前进度/下一步/坑（唯一进度真相）
6. 按当前任务读对应 SOP（微信系先读基本操作前置依赖）：
   - **网络预检（任何会改系统代理的采集前必读）**：`docs/guides/network-preflight.md`
   - **微信基本操作（前置依赖）**：`docs/guides/wechat-basic-operations.md`
   - 视频号采集：`docs/guides/wechat-channels-capture.md`
   - 公众号采集：`docs/guides/wechat-official-article.md`
   - 增量采集：`docs/guides/incremental-fetch.md`

读完用 `docs/项目维护SOP.md` §5「冷启动六问」自测，把六个答案讲给用户听，**答不上或文档自相矛盾先修文档再动手**。
开新任务窗口的固定动作（触发词、老窗口收口、标准句、兜底）见 `docs/新窗口接手开场白.md`。

### 1.2 续接（继续同一阶段的任务）
只读：
1. `project-management/active/TASK_STATUS.md` — 当前进度、下一步
2. `project-management/active/ISSUES.md` — 已知问题
3. 该工具的README或SOP相关小节

---

## 2. 核心规则

### 2.1 证书与代理（重要！多次踩坑）

> 采集前先跑只读预检 `python3 scripts/net_preflight.py`（`collect_channels.py --upstream auto` 已自动跑）；决策规则与跨机器配置见 `docs/guides/network-preflight.md`。

**正确操作**：
1. 证书相对可执行文件加载、已在系统钥匙串信任
2. 探针只对**默认路由的物理服务**（`route get default` → en0 = Ethernet，凭真实 MAC 判定）设代理；设置前快照、退出时**恢复原代理**（如 ClashX 的 7890），**永不触碰 Tailscale 等 utun/虚拟服务**
3. 捕获完成后探针 SIGTERM 自动恢复代理（禁 kill -9）

**Tailscale 共存规则（wj）**：
- Tailscale 未用 exit node，可常开、与采集共存；**不要开 exit node**，不要在探针运行（Ethernet=8899）瞬间切换 Tailscale
- Tailscale 服务若残留指向 8899 的死代理：stopped 时改不了（exit=5），须在 Tailscale 运行时跑 `bash scripts/fix_tailscale_proxy.sh`

**紧急恢复**（如果全网阻断）：
```bash
pkill -TERM -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done
```

### 2.2 问题驱动更新（强制）

发现任何问题（脚本bug、流程缺陷、文档缺失）时，必须立即评估是否需要更新文档或代码，不能只发现问题不更新。

### 2.3 变更影响分级处理（强制：先确认再执行）

- **L0 顺手修复**（错字、单处断链、单文件小错）：直接修复
- **L1 高扩散变更**（批量重命名/跨目录移动、≥5处引用级联、修改治理规范本身）：先出方案+影响清单，用户确认后执行
- **L2 架构/流程变更**：先和用户讨论，确认方案后执行
- 拿不准属于哪一级时，**就高不就低**

### 2.4 写文档前必须检查文档组织（强制）

遇到需要写文档时，必须先检查项目文档组织和分工：
1. `grep -r "关键词" docs/` 查找是否已有相关内容
2. 确认文档分工（见 `docs/DOCUMENTATION_MAP.md`）
3. WORKFLOW.md只放概览和链接，详细内容放各SOP

**防重复建设**：新建持久文档前，先列出它要承担的职责，指认现有权威源；已被承担则不新建。

### 2.5 大任务执行状态记录（强制）

**开始任何大任务前，必须先创建执行状态记录**：
1. 批量处理 >3个内容
2. 预计执行时间 >1小时
3. 涉及多个工具链

状态记录落点：`workspace/capture/state/`（不入库），`TASK_STATUS.md` 只更新指针级状态。

### 2.6 清理与维护原则

**核心价值观：以精简并删除历史冗余为荣，以堆砌重复实现为耻。**

- 新增脚本前检查是否已有同类实现；发现0引用的旧脚本主动清理
- 新增文档前检查职责是否已被现有文档承担；过时文档标注退役
- 空目录、空章节不保留
- **"不改写历史"的边界**：ADR/git历史只增不改；现行规范/活态台账完全过期的内容直接删改
- 文件和目录有变化时必须检查 .gitignore
- 提交前运行 `git status` 检查

### 2.7 提交前体检与交接（强制）

- `git commit` 前必须在仓库根跑 `python3 scripts/doc_health_check.py`，**0 ERROR 才提交**（WARN 记录后可放行）：查核心文件齐备、Markdown 断链、docs 文档登记、禁入内容（原始音视频/PDF/Office/明文凭证/临时票据）入库。
- 信息落点、维护节奏、冷启动六问统一见 `docs/项目维护SOP.md`；过程日志往 `docs/HANDOFF.md` §1 倒序追加。
- 用户说"开新窗口/换新窗口/新窗口接手"时，按 `docs/新窗口接手开场白.md` 收口，不自创交接长文。

---

## 3. 存储分工（硬约束）

| 位置 | 内容 | 说明 |
|------|------|------|
| GitHub仓库 | 代码+文档+清洗后知识成品 | **禁止**放视频、PDF、逐字转写、原文、凭证 |
| `library/` | 原始资源 + 知识成品 | 本地唯一权威源 |
| `workspace/` | 过程件 | gitignore忽略 |
| 百度网盘 | 成品镜像 | 备份+跨设备访问 |

> 详细目录结构见 `docs/DIRECTORY_STRUCTURE.md`

---

## 4. 工具快速索引

| 核心工具 | 位置 |
|---------|------|
| 视频捕获（MITM） | `platforms/wechat_channels/video-capture/` |
| 视频下载+解密 | `platforms/wechat_channels/video-downloader/` |
| 视频转文字 | `processing/transcription/tools/` |
| 图文OCR | `processing/ocr/tools/` |
| 知识库查询 | `processing/knowledge_extraction/tools/` |

---

## 5. 待办

当前待办详见 `project-management/active/TASK_STATUS.md`，本文档不重复维护。

---

*本文档随项目演进持续更新。发现规则缺失或不准确时，按"问题驱动更新"原则立即补充。*
