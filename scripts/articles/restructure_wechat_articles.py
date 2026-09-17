#!/usr/bin/env python3
"""
公众号图文重构脚本：将分散的正文JSON和图片，重构为每篇文章一个目录。

输入结构：
  正文/001_标题.json  (含content_text, content_html, images, image_ocr)
  图片/ae1116f40d0b55da.png  (hash命名，混在一起)

输出结构：
  001_标题/
    article.json    (元数据+OCR结果)
    content.md      (纯文本正文)
    content.html    (完整HTML，图片引用改为本地相对路径)
    images/
      01.png        (按顺序重命名)
      02.png

规则：
- 只保留图片完整的文章（所有引用的图片都存在）
- 孤儿图片（无文章引用）直接删除
- 无图文章也保留（纯文字文章）
"""

import json
import os
import re
import shutil
from pathlib import Path

BASE = Path("/Users/wenjiechen/Desktop/multiplatform-content-pipeline/library/06_articles/stock/顶底之王")
OLD_TEXT = BASE / "正文"
OLD_IMAGES = BASE / "图片"
NEW_DIR = BASE / "articles"

def main():
    # 收集所有图片
    all_images = {f.name: f for f in OLD_IMAGES.glob("*") if f.is_file()}
    print(f"原始图片数: {len(all_images)}")

    # 遍历所有文章
    articles = sorted(OLD_TEXT.glob("*.json"))
    print(f"原始文章数: {len(articles)}")

    kept = 0
    skipped_incomplete = 0
    skipped_no_content = 0
    total_images_moved = 0
    referenced_images = set()

    for article_file in articles:
        try:
            data = json.loads(article_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  跳过(解析失败): {article_file.name} - {e}")
            continue

        title = data.get("title", "").strip()
        content_text = data.get("content_text", "").strip()
        content_html = data.get("content_html", "").strip()
        image_ocr = data.get("image_ocr", [])

        # 跳过无正文的文章
        if not content_text and not content_html:
            print(f"  跳过(无正文): {article_file.name}")
            skipped_no_content += 1
            continue

        # 收集该文章引用的本地图片
        local_images = []
        for ocr in image_ocr:
            if isinstance(ocr, dict):
                fname = ocr.get("filename", "")
                if fname:
                    local_images.append(fname)

        # 检查图片完整性
        missing = [img for img in local_images if img not in all_images]
        if missing:
            print(f"  跳过(图片缺失{len(missing)}张): {article_file.name}")
            skipped_incomplete += 1
            continue

        # 创建文章目录
        # 使用原文件名（含序号）作为目录名，去掉.json
        dir_name = article_file.stem
        article_dir = NEW_DIR / dir_name
        images_dir = article_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # 复制并重命名图片
        image_remap = {}  # old_filename -> new_filename
        for idx, old_name in enumerate(local_images, 1):
            ext = Path(old_name).suffix.lower()
            new_name = f"{idx:02d}{ext}"
            src = all_images[old_name]
            dst = images_dir / new_name
            shutil.copy2(src, dst)
            image_remap[old_name] = new_name
            referenced_images.add(old_name)
            total_images_moved += 1

        # 修改HTML中的图片引用为本地相对路径
        new_html = content_html
        for old_name, new_name in image_remap.items():
            # 匹配远程URL中的图片
            for ocr in image_ocr:
                if isinstance(ocr, dict) and ocr.get("filename") == old_name:
                    old_url = ocr.get("url", "")
                    if old_url:
                        # 替换data-src和src
                        new_html = new_html.replace(old_url, f"images/{new_name}")
                        # 也替换可能的短URL
                        base_url = old_url.split("?")[0]
                        new_html = new_html.replace(base_url, f"images/{new_name}")

        # 也替换HTML中的hash文件名引用
        for old_name, new_name in image_remap.items():
            new_html = new_html.replace(old_name, f"images/{new_name}")

        # 写content.md
        (article_dir / "content.md").write_text(content_text, encoding="utf-8")

        # 写content.html
        (article_dir / "content.html").write_text(new_html, encoding="utf-8")

        # 写article.json（元数据，去掉大字段）
        article_meta = {
            "title": title,
            "author": data.get("author", ""),
            "publish_time": data.get("publish_time", ""),
            "url": data.get("url", ""),
            "content_length": data.get("content_length", 0),
            "image_count": len(local_images),
            "image_ocr": image_ocr,
            "image_remap": image_remap,
        }
        (article_dir / "article.json").write_text(
            json.dumps(article_meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        kept += 1
        if kept % 50 == 0:
            print(f"  已处理 {kept} 篇...")

    print(f"\n=== 重构完成 ===")
    print(f"保留文章: {kept}")
    print(f"跳过(无正文): {skipped_no_content}")
    print(f"跳过(图片缺失): {skipped_incomplete}")
    print(f"移动图片: {total_images_moved}")
    print(f"被引用图片: {len(referenced_images)}")
    print(f"孤儿图片(将删除): {len(all_images) - len(referenced_images)}")

    # 删除旧目录
    print(f"\n删除旧的正文目录: {OLD_TEXT}")
    shutil.rmtree(OLD_TEXT)
    print(f"删除旧的图片目录: {OLD_IMAGES}")
    shutil.rmtree(OLD_IMAGES)

    print(f"\n新目录: {NEW_DIR}")
    print(f"新文章数: {len(list(NEW_DIR.glob('*')))}")

if __name__ == "__main__":
    main()
