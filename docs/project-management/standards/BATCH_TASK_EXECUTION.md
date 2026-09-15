# 批量任务执行规范（BATCH_TASK_EXECUTION）

> **文档类型**：Standard（规范 — 批量任务执行）
> **更新频率**：流程变更时
> **维护者**：AI自动维护
> **读者**：AI代理（执行批量任务前必读）

> 本文档定义批量任务的执行状态记录、异常恢复、进度跟踪规范。
> 设计参考高顿CPA项目BATCH_TASK_EXECUTION.md，根据本项目特点简化。

---

## 1. 什么时候需要创建执行状态记录

满足任一条件即必须创建：
1. 批量处理 >3 个视频/文章
2. 预计执行时间 >1 小时
3. 涉及多个工具链（捕获 + 下载 + 解密 + 转写等）
4. 用户明确要求"批量处理"、"全部完成"

---

## 2. 状态记录落点

| 层级 | 位置 | 内容 |
|------|------|------|
| 批次明细 | `data/_workspace/capture/state/` | 具体进度、断点、锁文件（不入库） |
| 指针级状态 | `project-management/active/TASK_STATUS.md` | 只更新工单状态，不抄批次明细 |
| 问题记录 | `project-management/active/ISSUES.md` | 机制级问题（换平台还会踩的） |

**原则**：TASK_STATUS.md 是"当前做什么、到哪"的唯一进度真相，但只放指针，不放批次明细。

---

## 3. 状态记录格式

### 3.1 批次状态文件（JSON）

```json
{
  "batch_id": "capture_20260915_001",
  "task_type": "video_download",
  "started_at": "2026-09-15T10:00:00+08:00",
  "updated_at": "2026-09-15T10:30:00+08:00",
  "status": "running",
  "total": 313,
  "completed": 150,
  "failed": 2,
  "skipped": 0,
  "current_item": "短视频_150_xxx.mp4",
  "failed_items": [
    {"name": "短视频_023_xxx.mp4", "reason": "下载超时", "retry_count": 3}
  ]
}
```

### 3.2 进度文件（JSONL，支持增量写入）

```
{"time": "2026-09-15T10:01:00", "action": "start", "item": "短视频_001"}
{"time": "2026-09-15T10:02:00", "action": "complete", "item": "短视频_001", "duration": 45}
{"time": "2026-09-15T10:03:00", "action": "start", "item": "短视频_002"}
```

### 3.3 锁文件

- 位置：`data/_workspace/capture/state/<task_type>.lock`
- 内容：PID + 启动时间
- 作用：防止多进程冲突
- 任务完成后必须删除锁文件

---

## 4. 异常恢复流程

### 4.1 中断检测

1. 检查锁文件是否存在
2. 检查锁文件中的PID是否还在运行
3. 如果PID不存在但锁文件存在 → 异常中断，需要恢复

### 4.2 恢复步骤

1. 读取批次状态文件，获取已完成数量和失败项
2. 从断点继续（跳过已完成项）
3. 重试失败项（最多3次）
4. 更新状态文件

### 4.3 紧急恢复命令

```bash
# 视频捕获工具异常退出，清除系统代理
pkill -9 -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done

# 清除残留锁文件
rm -f data/_workspace/capture/state/*.lock
```

---

## 5. 必须立即更新TASK_STATUS.md的场景

1. 任务开始时（更新状态为"进行中"）
2. 每个子任务完成时（更新进度）
3. 任务完成时（更新状态为"完成"）
4. 遇到问题或阻塞时（更新问题描述）
5. 项目结构/文档体系/工具链有重大变更时
6. 每次git提交前（检查任务状态是否最新）

**更新要求**：必须立即更新，不得延迟到"以后再更新"。

---

## 6. 批量任务分类与典型流程

### 6.1 视频采集批次

```
启动捕获工具 → 微信滚动列表 → 停止捕获 → URL清单 → 批量下载 → 解密 → 验证 → 归档
```

状态记录：`data/_workspace/capture/state/capture_<date>.json`

### 6.2 转写批次

```
读取视频列表 → 跳过已转写 → 批量转写 → 验证转写稿非空 → 更新状态
```

状态记录：`data/_workspace/capture/state/transcribe_<date>.json`

### 6.3 OCR批次

```
读取文章图片列表 → 跳过已OCR → 批量OCR → 更新文章JSON → 验证
```

状态记录：`data/_workspace/capture/state/ocr_<date>.json`

---

## 7. 性能与资源保护

1. 单次批次不超过 500 个项目（超过则分批）
2. 下载并发数不超过 5（避免触发风控）
3. 转写单进程运行（FunASR占用资源大）
4. 每处理 50 个项目保存一次状态（防止崩溃丢失进度）
5. 失败项最多重试 3 次，超过则记录到失败清单

---

## 8. 完成标准

批量任务完成后必须验证：
- [ ] 所有项目都已处理（总数 = 已完成 + 已跳过）
- [ ] 失败项有明确原因记录
- [ ] 状态文件已更新为"完成"
- [ ] 锁文件已删除
- [ ] TASK_STATUS.md 已更新
- [ ] 临时文件已清理
- [ ] 按 DOC_SYNC_CHECKLIST.md 同步相关文档

---

*最后更新：2026-09-15*
