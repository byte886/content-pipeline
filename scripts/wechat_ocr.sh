#!/usr/bin/env bash
# 微信UI通用OCR工具（底层自动适配RapidOCR/ Vision，后续升级只改本文件）
# 用法：
# 1. 对指定图片做OCR输出纯文本: ./wechat_ocr.sh <图片路径>
# 2. 对全屏做临时截图再OCR: ./wechat_ocr.sh --screen
# 3. 判断屏幕上是否存在指定文字: ./wechat_ocr.sh --has "搜索网络"
set -euo pipefail
OCR_SWIFT="/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
TMP_IMG="/tmp/wechat_ocr_tmp.png"

if [ "$1" == "--screen" ]; then
  screencapture -x -C "$TMP_IMG"
  swift "$OCR_SWIFT" "$TMP_IMG"
  rm -f "$TMP_IMG"
elif [ "$1" == "--has" ]; then
  target="$2"
  screencapture -x -C "$TMP_IMG"
  res=$(swift "$OCR_SWIFT" "$TMP_IMG")
  rm -f "$TMP_IMG"
  if echo "$res" | grep -q "$target"; then
    echo "FOUND"
    exit 0
  else
    echo "NOT_FOUND"
    exit 1
  fi
else
  img="$1"
  swift "$OCR_SWIFT" "$img"
fi
