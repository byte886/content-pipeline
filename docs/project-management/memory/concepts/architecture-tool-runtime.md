---
concept: architecture-tool-runtime
title: 工具运行目录与证书信任
tags: [architecture, tools, certificate]
verified: machine
---

# 工具运行目录与证书信任

## 结论

**捕获工具必须从`tools/video-capture/`目录运行**，否则会生成新的未信任证书，导致TLS握手失败、全网阻断。

## 关键规则

1. **证书路径**：`tools/video-capture/ca.crt`（已在系统钥匙串信任）
2. **运行目录**：必须在`tools/video-capture/`下执行`./video-capture`
3. **禁止**：从项目根目录运行`./tools/video-capture/video-capture`（会在根目录生成新ca.crt）
4. **检查**：启动前确认项目根目录**没有**ca.crt/ca.key（如果有说明运行目录错了）

## 紧急恢复（全网阻断时）

```bash
pkill -9 -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done
```

## 来源与下钻

- 证书问题详细：`project-management/active/ISSUES.md` ISSUE-001
- 代理设置：`tools/video-capture/proxy_darwin.go`
- 捕获工具SOP：`docs/视频号内容采集SOP.md`
