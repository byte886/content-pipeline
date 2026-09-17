#!/usr/bin/env python3
"""
批量获取公众号文章正文（Playwright浏览器方案）
- 用真实浏览器访问，绕过微信验证码
- 断点续传（已获取的跳过）
- 失败重试（最多3次）
- 控制请求频率（每篇间隔2秒）
"""

import json
import os
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 配置
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL_LIST = os.environ.get("ARTICLE_URL_LIST", os.path.join(PROJECT_DIR, "library/00_manifest/文章URL列表.json"))
# TODO: 重构为每篇文章一个目录结构（articles/<序号>_标题/{article.json,content.md,content.html,images/}）
# 当前仍使用旧的分散存储，后续需改造
OUTPUT_DIR = os.environ.get("ARTICLE_OUTPUT_DIR", os.path.join(PROJECT_DIR, "library/06_articles/stock/顶底之王/_legacy/正文"))
IMAGE_DIR = os.environ.get("ARTICLE_IMAGE_DIR", os.path.join(PROJECT_DIR, "library/06_articles/stock/顶底之王/_legacy/图片"))
PROGRESS_FILE = os.environ.get("ARTICLE_PROGRESS_FILE", os.path.join(PROJECT_DIR, "workspace/capture/article_fetch_progress.json"))

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "captcha": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def safe_filename(title, max_len=80):
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = re.sub(r'\s+', ' ', title).strip()
    if len(title) > max_len:
        title = title[:max_len]
    return title

def fetch_article(page, url, max_retries=3):
    """用浏览器获取单篇文章"""
    for attempt in range(max_retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)  # 等待页面渲染

            # 检查是否触发验证码
            if "captcha" in page.url or "appmsgcaptcha" in page.url:
                print(f"  ⚠️ 触发验证码，等待5秒后重试...")
                time.sleep(5)
                continue

            # 等待正文加载
            try:
                page.wait_for_selector("#js_content", timeout=10000)
            except:
                pass

            # 提取文章信息
            result = page.evaluate("""() => {
                const title = document.querySelector('#activity-name')?.textContent?.trim() || '';
                const author = document.querySelector('.rich_media_meta_text')?.textContent?.trim() || '';
                const pubTime = document.querySelector('#publish_time')?.textContent?.trim() || '';
                const content = document.querySelector('#js_content')?.innerText || '';

                // 提取图片
                const images = [];
                document.querySelectorAll('#js_content img').forEach(img => {
                    const src = img.getAttribute('data-src') || img.src;
                    if (src && src.startsWith('http')) images.push(src);
                });

                return {title, author, pubTime, content, images};
            }""")

            if result and result['content']:
                result['url'] = url
                result['fetched_at'] = datetime.now().isoformat()
                return result
            else:
                print(f"  正文为空，重试 {attempt+1}/{max_retries}")

        except Exception as e:
            print(f"  请求失败: {e}, 重试 {attempt+1}/{max_retries}")

        time.sleep(3 * (attempt + 1))

    return None

def save_article(article, date_str):
    filename = f"{date_str}_{safe_filename(article['title'])}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    md_content = f"""# {article['title']}

> 作者：{article['author']}
> 发布时间：{article['pubTime']}
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
    with open(URL_LIST, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"共 {len(articles)} 篇文章")

    progress = load_progress()
    completed_set = set(progress["completed"])

    todo = [a for a in articles if a['url'] not in completed_set]
    print(f"待获取: {len(todo)} 篇（已完成: {len(completed_set)}）")

    success_count = 0
    fail_count = 0
    captcha_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, article in enumerate(todo, 1):
            url = article['url']
            title = article['title'][:40]
            date_str = article.get('date', 'unknown')

            print(f"[{i}/{len(todo)}] [{date_str}] {title}")

            result = fetch_article(page, url)

            if result:
                filepath = save_article(result, date_str)
                progress["completed"].append(url)
                success_count += 1
                print(f"  ✓ 已保存 ({len(result['content'])}字, {len(result['images'])}张图)")
            else:
                # 检查是否是验证码
                if "captcha" in page.url:
                    progress["captcha"].append(url)
                    captcha_count += 1
                    print(f"  ⚠️ 验证码拦截，已记录")
                else:
                    progress["failed"].append(url)
                    fail_count += 1
                    print(f"  ✗ 获取失败")

            save_progress(progress)

            if i < len(todo):
                time.sleep(2)

            # 每50篇重启浏览器，避免内存泄漏
            if i % 50 == 0:
                print(f"  重启浏览器...")
                browser.close()
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()

        browser.close()

    print(f"\n=== 完成 ===")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"验证码拦截: {captcha_count}")
    print(f"累计完成: {len(progress['completed'])}")

if __name__ == "__main__":
    main()
