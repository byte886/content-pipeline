# AGENTS.md — AI代理操作手册

> **文档类型**：Governance（治理规范 — AI操作手册）
> **维护者**：AI自动维护 + 用户审核
> **读者**：AI代理（每次启动自动加载）

> 本文档是AI代理的操作手册，命令式、可执行。执行任何任务前必须先阅读本文档对应部分。

---

## 1. 项目概览

**项目目标**：构建A股投资知识库，自动化采集微信视频号「交易的游戏」（证券投资顾问刘广义，关联公众号「顶底之王」）的全部短视频、直播回放和公众号文章，经过转写/OCR/知识提取后，形成结构化知识库，为量化系统和内容创作提供基础。

**核心数据**：
- 短视频：313个（已下载+转写）
- 直播回放：23个（已下载，待转写）
- 公众号文章：277篇（已下载，275篇有正文，910张图片已OCR）

---

## 2. 执行前必读

### 2.1 冷启动（首次接触/跨阶段切换）
按序读：
1. `docs/DOCUMENTATION_MAP.md` — 文档地图（快速入口，先读这个）
2. `docs/DIRECTORY_STRUCTURE.md` — 目录结构与存储分工
3. `docs/project-management/memory/index.md` — 工程记忆（跨会话稳定结论）
4. `project-management/active/TASK_STATUS.md` + `active/ISSUES.md` — 当前状态
5. 对应环节的SOP：
   - 视频采集：`docs/视频号内容采集SOP.md`
   - 文章采集：`docs/公众号文章采集SOP.md`
   - 高质量URL：`docs/高质量URL研究.md`
   - API研究：`docs/视频号API研究.md`

### 2.2 续接（继续同一阶段的任务）
只读：
1. `project-management/active/TASK_STATUS.md` — 当前进度、下一步
2. `project-management/active/ISSUES.md` — 已知问题
3. `docs/DOCUMENTATION_MAP.md` — 找到对应工具和文档
4. 该工具的README或SOP相关小节

---

## 3. 核心规则

### 3.1 证书与代理（重要！多次踩坑，已修复）

**已修复**：捕获工具现在使用**相对于可执行文件的路径**加载证书（`os.Executable()`），无论从哪个目录运行都能正确加载`tools/video-capture/ca.crt`。

**历史问题**：之前用相对路径`ca.crt`，从项目根目录运行时会生成新的未信任证书，导致TLS握手失败、全网阻断。

**正确操作**：
1. 可以从任意目录运行`./tools/video-capture/video-capture`
2. 证书路径：`tools/video-capture/ca.crt`（已在系统钥匙串信任）
3. 启动前检查：项目根目录**不应**有ca.crt/ca.key（如果有说明是旧版本生成的，删除即可）
4. 捕获完成后必须清除系统代理（工具退出时自动清除）

**紧急恢复**（如果全网阻断）：
```bash
pkill -9 -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done
```

### 3.2 工具运行目录规范

| 工具 | 运行目录 | 原因 |
|------|---------|------|
| video-capture | 任意目录 | 已修复，使用相对于可执行文件的路径加载证书 |
| 其他Python脚本 | 项目根目录 | 相对路径引用data/和knowledge-base/ |

### 3.3 问题驱动更新
发现任何问题（脚本bug、流程缺陷、文档缺失）必须立即评估并更新文档或代码，不能只发现不修复。

### 3.4 存储分工（硬约束）

| 位置 | 内容 | 说明 |
|------|------|------|
| GitHub仓库 | 代码+文档 | **禁止**放视频、PDF、文字稿等大文件 |
| `data/videos/` | 视频原始文件 | gitignore忽略 |
| `data/transcripts/` | 转写稿 | gitignore忽略 |
| `knowledge-base/` | 结构化知识成品 | 部分入库（正文JSON、图片映射） |
| 百度网盘 | 与本地完全镜像 | 备份+跨设备访问 |

### 3.5 后台任务管理
- 长时间运行的任务（转写/OCR/下载）必须用`nohup`后台运行
- 日志输出到`/tmp/`目录
- 启动后立即记录PID和日志路径
- 完成后检查退出码和输出

---

## 4. 工具快速索引

> 完整清单见 `docs/DOCUMENTATION_MAP.md`「工具清单」

| 任务 | 工具 | 位置 |
|------|------|------|
| 视频捕获（MITM） | video-capture | `tools/video-capture/` |
| 视频下载+解密 | batch_download_v4.py | `tools/video-downloader/` |
| 自动化采集 | auto_capture.py | `tools/auto-capture/` |
| 增量采集 | incremental_collect.py | `tools/auto-capture/` |
| 视频转文字 | batch_transcribe.py | `tools/transcription/` |
| 图文OCR | batch_article_images.py | `tools/ocr/` |
| 知识提取 | extract_knowledge.py | `tools/knowledge-extraction/` |
| 知识库查询 | knowledge_base.py | `tools/knowledge-extraction/` |
| 文章采集 | fetch_articles_*.py | `scripts/article/`（待迁移） |
| 网盘同步 | sync_stock.sh | `scripts/netdisk/` |

---

## 5. 常见问题

### Q: 为什么捕获工具启动后全网断了？
A: 证书路径问题。检查项目根目录是否有ca.crt，如果有说明运行目录错了。删除根目录的ca.crt，从`tools/video-capture/`目录运行。

### Q: 视频下载后无法播放？
A: 短视频是加密的，需要用DecodeKey解密。直播回放不需要解密。运行`node tools/video-downloader/wechat_decrypt.js <decodeKey> <file>`。

### Q: 下载的视频只有2-5MB，太小了？
A: 默认是低分辨率版本。用`quality=max`参数下载xWT111格式（大69%）。真正的原始高清版本尚未找到，见`docs/高质量URL研究.md`。

### Q: 转写输出在哪里？
A: `data/transcripts/短视频/{视频名}/transcript.md`（注意是子目录，不是直接md文件）。

---

## 6. 待办与已知限制

- [ ] 直播回放23个尚未转写
- [ ] 方案B（视频号API）尚未实际验证
- [ ] 高质量URL（原始48MB版本）尚未找到
- [ ] scripts/article/ 待迁移到 tools/ 下统一管理
- [ ] 知识提取当前是规则版，待接入LLM深度提取
- [ ] 知识库与量化系统对接尚未实现

---

*本文档随项目演进持续更新。发现规则缺失或不准确时，按"问题驱动更新"原则立即补充。*
