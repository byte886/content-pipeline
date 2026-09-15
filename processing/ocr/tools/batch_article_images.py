#!/usr/bin/env python3
"""
公众号文章图片批量下载与OCR脚本

功能：
1. 遍历所有文章JSON，提取图片URL
2. 下载图片（去重）
3. 用macOS Vision OCR识别
4. 将OCR结果保存到文章JSON中

用法：
    python3 batch_article_images.py --articles <文章目录> --images <图片目录> [--ocr]
    python3 batch_article_images.py --articles ... --images ... --download-only
    python3 batch_article_images.py --articles ... --images ... --ocr-only
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
import urllib.request


OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
OCR_BINARY = "/tmp/ocr_vision_bin"  # 编译后的二进制，速度快10倍


def url_to_filename(url):
    """将URL转换为文件名（用hash避免特殊字符）"""
    parsed = urlparse(url)
    # 用URL的hash作为文件名
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    # 尝试从URL获取扩展名
    ext = '.png'
    if 'wx_fmt=gif' in url:
        ext = '.gif'
    elif 'wx_fmt=jpeg' in url or 'wx_fmt=jpg' in url:
        ext = '.jpg'
    elif 'wx_fmt=png' in url:
        ext = '.png'
    return f"{url_hash}{ext}"


def download_image(url, output_path, max_retries=3):
    """下载单张图片"""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
        return True, "已存在"

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://mp.weixin.qq.com/'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
                if len(data) > 100:
                    with open(output_path, 'wb') as f:
                        f.write(data)
                    return True, f"下载成功 ({len(data)} bytes)"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return False, str(e)
    return False, "重试失败"


def ocr_image(image_path):
    """对单张图片进行OCR"""
    try:
        # 优先使用编译后的二进制（速度快10倍）
        if os.path.exists(OCR_BINARY):
            cmd = [OCR_BINARY, image_path]
        else:
            cmd = ['swift', OCR_SCRIPT, image_path]

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            if text and text != "未识别到文字":
                return text
        return ""
    except subprocess.TimeoutExpired:
        return "OCR超时"
    except Exception as e:
        return f"OCR错误: {e}"


def main():
    parser = argparse.ArgumentParser(description='公众号文章图片批量下载与OCR')
    parser.add_argument('--articles', required=True, help='文章JSON目录')
    parser.add_argument('--images', required=True, help='图片保存目录')
    parser.add_argument('--download-only', action='store_true', help='只下载图片')
    parser.add_argument('--ocr-only', action='store_true', help='只OCR已下载的图片')
    parser.add_argument('--workers', type=int, default=5, help='下载线程数')
    args = parser.parse_args()

    article_dir = Path(args.articles)
    image_dir = Path(args.images)
    image_dir.mkdir(parents=True, exist_ok=True)

    # 1. 收集所有图片URL
    print("=== 收集图片URL ===")
    all_images = {}  # url -> {filename, articles: []}
    article_images = {}  # article_file -> [urls]

    for article_file in sorted(article_dir.glob('*.json')):
        with open(article_file) as f:
            data = json.load(f)
        images = data.get('images', [])
        if images:
            article_images[article_file.name] = images
            for url in images:
                filename = url_to_filename(url)
                if url not in all_images:
                    all_images[url] = {
                        'filename': filename,
                        'articles': []
                    }
                all_images[url]['articles'].append(article_file.name)

    print(f"文章数: {len(article_images)}")
    print(f"图片URL数: {len(all_images)}")

    # 2. 下载图片
    if not args.ocr_only:
        print(f"\n=== 下载图片 ({len(all_images)}张, {args.workers}线程) ===")
        download_results = {'success': 0, 'failed': 0, 'skipped': 0}

        def download_task(url, info):
            output_path = image_dir / info['filename']
            success, msg = download_image(url, str(output_path))
            return url, success, msg

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(download_task, url, info): url
                for url, info in all_images.items()
            }
            for i, future in enumerate(as_completed(futures), 1):
                url, success, msg = future.result()
                if success:
                    if "已存在" in msg:
                        download_results['skipped'] += 1
                    else:
                        download_results['success'] += 1
                else:
                    download_results['failed'] += 1
                if i % 50 == 0:
                    print(f"  进度: {i}/{len(all_images)} - 成功:{download_results['success']} 跳过:{download_results['skipped']} 失败:{download_results['failed']}")

        print(f"下载完成: 成功={download_results['success']} 跳过={download_results['skipped']} 失败={download_results['failed']}")

    # 3. OCR识别
    if not args.download_only:
        print(f"\n=== OCR识别 ===")
        ocr_results = {}  # filename -> text
        ocr_count = 0
        ocr_success = 0

        # 建立url->filename映射
        url_to_file = {url: info['filename'] for url, info in all_images.items()}

        for url, info in all_images.items():
            filename = info['filename']
            image_path = image_dir / filename

            if not image_path.exists() or os.path.getsize(image_path) < 100:
                continue

            ocr_count += 1
            text = ocr_image(str(image_path))
            if text and not text.startswith("OCR"):
                ocr_results[filename] = text
                ocr_success += 1

            if ocr_count % 10 == 0:
                print(f"  进度: {ocr_count}/{len(all_images)} - 有文字:{ocr_success}", flush=True)

        print(f"OCR完成: 处理={ocr_count} 有文字={ocr_success}")

        # 4. 将OCR结果保存到文章JSON中
        print(f"\n=== 更新文章JSON ===")
        updated = 0
        for article_file, urls in article_images.items():
            file_path = article_dir / article_file
            with open(file_path) as f:
                data = json.load(f)

            image_ocr = []
            for url in urls:
                filename = url_to_filename(url)
                if filename in ocr_results:
                    image_ocr.append({
                        'url': url,
                        'filename': filename,
                        'ocr_text': ocr_results[filename]
                    })

            if image_ocr:
                data['image_ocr'] = image_ocr
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                updated += 1

        print(f"更新了 {updated} 篇文章")

    # 5. 保存图片URL映射
    mapping_file = image_dir / 'image_url_mapping.json'
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump({
            url: {'filename': info['filename'], 'articles': info['articles']}
            for url, info in all_images.items()
        }, f, ensure_ascii=False, indent=2)
    print(f"\n图片映射已保存: {mapping_file}")


if __name__ == '__main__':
    main()
