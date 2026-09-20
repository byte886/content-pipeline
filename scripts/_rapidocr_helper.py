#!/usr/bin/env python3
# 全局RapidOCR统一调用辅助脚本（和work-doc-extract技能共用同一套OCR能力）
import sys
from rapidocr import RapidOCR

ocr = RapidOCR()
img_path = sys.argv[1]
result = ocr(img_path)
# 输出所有识别到的文字行
for line in result.txts:
    print(line)
