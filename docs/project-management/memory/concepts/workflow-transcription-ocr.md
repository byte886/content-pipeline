---
concept: workflow-transcription-ocr
title: 视频转文字与OCR链路
tags: [workflow, transcription, ocr]
verified: machine
---

# 视频转文字与OCR链路

## 结论

- **视频转文字**：FunASR本地离线转写（支持中/英/日/韩/粤），9.7x实时速度
- **图文OCR**：macOS Vision框架，编译为二进制后1.5秒/张

## 关键规则

1. **转写输出格式**：`library/04_transcript/wechat_channels/短视频/{视频名}/transcript.md`（子目录，不是直接md文件）
2. **OCR提速**：必须先用`swiftc -O`编译为二进制，不能用swift解释执行（每次都要编译，极慢）
3. **OCR二进制位置**：`/tmp/ocr_vision_bin`（38K，1.5秒/张）
4. **有文本层不OCR**：PDF/DOCX等有文本层的直接解析，不OCR

## 来源与下钻

- 转写工具：`processing/transcription/tools/batch_transcribe.py`
- OCR工具：`processing/ocr/tools/batch_article_images.py`
- 自定义技能：`/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/`（FunASR）
- 自定义技能：`/Users/wenjiechen/Doubao/skills/work-doc-extract/`（OCR）
