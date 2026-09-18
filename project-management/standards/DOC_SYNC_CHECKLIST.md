# 文档同步检查清单（DOC_SYNC_CHECKLIST）

> **文档类型**：Standard（规范 — 检查清单）
> **维护者**：AI自动维护

---

## 同步时机

必须执行本清单的场景：
1. 完成采集/转写/OCR批次后
2. 项目结构调整后（新增/删除/移动文件）
3. 发现问题并解决后
4. 每次git提交前

---

## 检查清单

### 一、任务状态同步
- [ ] `active/TASK_STATUS.md` 已更新（工单状态、下一步）
- [ ] `active/ISSUES.md` 已更新（新问题记录、已解决问题关闭）

### 二、文档关联同步
- [ ] `DOCUMENTATION_MAP.md` 已更新（新增/删除文档）
- [ ] `WORKFLOW.md` 已更新（如流程变更）
- [ ] `REQUIREMENTS.md` 已更新（如需求变更）

### 三、目录结构同步
- [ ] `DIRECTORY_STRUCTURE.md` 已更新（新增/删除目录）
- [ ] `.gitignore` 已检查，`git status` 确认没有不该提交的文件

### 四、工具与脚本同步
- [ ] 新增脚本已加入 DOCUMENTATION_MAP 工具清单
- [ ] 删除脚本已从文档中移除引用

---

## 快速检查命令

```bash
git status
grep -r "TODO\|待补充\|待完善" docs/ project-management/ AGENTS.md
find . -type d -empty -not -path "./.git/*"
```

---

## 核心原则

1. **问题驱动更新**：发现问题立即评估是否需要更新文档
2. **不抄易变计数**：已下载多少以现场文件为准，不抄进文档
3. **提交前必查**：每次git提交前必须跑一遍本清单

---

*最后更新：2026-09-17*
