#!/usr/bin/env python3
"""
批量获取公众号文章正文
- 读取文章URL列表
- 逐篇获取正文，保存为Markdown
- 断点续传（已获取的跳过）
- 失败重试（最多3次）
- 控制请求频率（每篇间隔1.5秒）
"""

import json
import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 配置
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL_LIST = os.environ.get("ARTICLE_URL_LIST", os.path.join(PROJECT_DIR, "library/00_manifest/文章URL列表.json"))
# TODO: 重构为每篇文章一个目录结构（articles/<序号>_标题/{article.json,content.md,content.html,images/}）
OUTPUT_DIR = os.environ.get("ARTICLE_OUTPUT_DIR", os.path.join(PROJECT_DIR, "library/06_articles/stock/顶底之王/_legacy/正文"))
IMAGE_DIR = os.environ.get("ARTICLE_IMAGE_DIR", os.path.join(PROJECT_DIR, "library/06_articles/stock/顶底之王/_legacy/图片"))
PROGRESS_FILE = os.environ.get("ARTICLE_PROGRESS_FILE", os.path.join(PROJECT_DIR, "workspace/capture/article_fetch_progress.json"))

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "current": None}

def save_progress(progress):
    """保存进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def safe_filename(title, max_len=80):
    """生成安全的文件名"""
    # 移除非法字符
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = re.sub(r'\s+', ' ', title).strip()
    if len(title) > max_len:
        title = title[:max_len]
    return title

def fetch_article(url, max_retries=3):
    """获取单篇文章正文"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return parse_article(resp.text, url)
            else:
                print(f"  HTTP {resp.status_code}, 重试 {attempt+1}/{max_retries}")
        except Exception as e:
            print(f"  请求失败: {e}, 重试 {attempt+1}/{max_retries}")
        time.sleep(2 * (attempt + 1))
    return None

def parse_article(html, url):
    """解析文章HTML，提取正文"""
    soup = BeautifulSoup(html, 'html.parser')

    # 标题
    title_elem = soup.find('h1', id='activity-name')
    title = title_elem.get_text(strip=True) if title_elem else "无标题"

    # 作者
    author_elem = soup.find('span', class_='rich_media_meta rich_media_meta_text')
    author = author_elem.get_text(strip=True) if author_elem else ""

    # 发布时间
    time_elem = soup.find('em', id='publish_time')
    pub_time = time_elem.get_text(strip=True) if time_elem else ""

    # 正文
    content_elem = soup.find('div', id='js_content')
    if not content_elem:
        return None

    # 提取正文文本和图片
    content_text = []
    images = []

    for elem in content_elem.descendants:
        if elem.name == 'p':
            text = elem.get_text(strip=True)
            if text:
                content_text.append(text)
        elif elem.name == 'img':
            img_url = elem.get('data-src') or elem.get('src')
            if img_url and img_url.startswith('http'):
                images.append(img_url)
        elif elem.name == 'section':
            # section里的文本
            pass

    # 也可以直接获取所有文本
    full_text = content_elem.get_text(separator='\n', strip=True)

    return {
        "title": title,
        "author": author,
        "pub_time": pub_time,
        "url": url,
        "content": full_text,
        "paragraphs": content_text,
        "images": images,
        "fetched_at": datetime.now().isoformat(),
    }

def save_article(article, date_str):
    """保存文章为Markdown"""
    filename = f"{date_str}_{safe_filename(article['title'])}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    md_content = f"""# {article['title']}

> 作者：{article['author']}
> 发布时间：{article['pub_time']}
> 原文链接：{article['url']}
> 抓取时间：{article['fetched_at']}

---

{article['content']}

---

## 图片链接（{len(article['images'])}张）

"""
    for i, img_url in enumerate(article['images'], 1):
        md_content += f"{i}. {img_url}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return filepath

def main():
    # 读取URL列表
    with open(URL_LIST, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"共 {len(articles)} 篇文章")

    # 加载进度
    progress = load_progress()
    completed_set = set(progress["completed"])
    failed_set = set(progress["failed"])

    # 过滤掉已完成的
    todo = [a for a in articles if a['url'] not in completed_set]
    print(f"待获取: {len(todo)} 篇（已完成: {len(completed_set)}，失败: {len(failed_set)}）")

    success_count = 0
    fail_count = 0

    for i, article in enumerate(todo, 1):
        url = article['url']
        title = article['title'][:40]
        date_str = article.get('date', 'unknown')

        print(f"[{i}/{len(todo)}] [{date_str}] {title}")

        result = fetch_article(url)

        if result:
            filepath = save_article(result, date_str)
            progress["completed"].append(url)
            success_count += 1
            print(f"  ✓ 已保存: {os.path.basename(filepath)} ({len(result['images'])}张图)")
        else:
            progress["failed"].append(url)
            fail_count += 1
            print(f"  ✗ 获取失败")

        # 保存进度
        save_progress(progress)

        # 控制频率
        if i < len(todo):
            time.sleep(1.5)

    print(f"\n=== 完成 ===")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"累计完成: {len(progress['completed'])}")
    print(f"累计失败: {len(progress['failed'])}")

if __name__ == "__main__":
    main()
