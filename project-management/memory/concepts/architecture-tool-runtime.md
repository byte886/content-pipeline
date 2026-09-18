---
concept: architecture-tool-runtime
title: 工具运行目录与证书信任
tags: [architecture, tools, certificate]
verified: machine
---

# 工具运行目录与证书信任

## 结论

**捕获工具可从任意目录运行**（证书路径已修复为相对于可执行文件的路径，`os.Executable()+filepath.Dir()`）。证书与二进制同目录，不会因运行目录不同而生成新证书。

## 关键规则

1. **证书位置**：`platforms/wechat_channels/video-capture/ca.crt`（与二进制同目录，已在系统钥匙串信任）
2. **运行目录**：任意目录均可，执行 `./platforms/wechat_channels/video-capture/video-capture`
3. **禁止**：删除或替换 `ca.crt/ca.key`（会导致TLS握手失败）
4. **检查**：启动前确认 `ca.crt` 存在且与二进制同目录

## 紧急恢复（全网阻断时）

```bash
pkill -9 -f video-capture
for s in "Ethernet" "Wi-Fi"; do
  networksetup -setwebproxystate "$s" off
  networksetup -setsecurewebproxystate "$s" off
done
```

## 来源与下钻

- 证书问题历史：`project-management/active/ISSUES.md` ISSUE-001（已解决）
- 代理设置：`platforms/wechat_channels/video-capture/proxy_darwin.go`
- 捕获工具SOP：`docs/guides/wechat-channels-capture.md`
- ADR决策：`project-management/decisions/ADR-002-视频号采集的证书与代理方案.md`
