---
concept: workflow-video-capture
title: 视频号采集链路
tags: [workflow, video, capture]
verified: machine
---

# 视频号采集链路

## 结论

采集链路：**MITM捕获 → 下载 → 解密 → 验证 → 去重**

## 关键参数

- **高质量URL**：`X-snsvideoflag=xWT111`（最大3.92MB，比默认xWT113的2.32MB大69%）
- **6种格式大小**：xWT111(3.92MB) > xWT112(3.01MB) > xWT126(2.68MB) > xWT113(2.32MB默认) > xWT127(2.15MB) > xWT128(1.63MB)
- **解密原理**：DecodeKey → ISAAC64生成128KB数组 → XOR文件前128KB
- **直播回放**：无DecodeKey，无需解密

## 已验证做不通

- 只保留encfilekey+token参数 → 下载0字节
- idx参数修改 → 返回相同大小
- 原始48.5MB高清版本 → 尚未找到

## 来源与下钻

- 采集SOP：`docs/视频号内容采集SOP.md`
- 高质量URL研究：`docs/高质量URL研究.md`
- 下载工具：`tools/video-downloader/batch_download_v4.py`
- 解密工具：`tools/video-downloader/wechat_decrypt.js`
