#!/usr/bin/env python3
"""
mitmproxy响应捕获脚本：自动捕获微信公众号文章正文
- 当微信内置浏览器打开文章时，自动捕获响应
- 用正则解析HTML（不依赖bs4，兼容mitmproxy内置Python环境）
- 保存为Markdown
"""

import mitmproxy.http
import json
import os
import re
import time
from datetime import datetime

OUTPUT_DIR = os.environ.get("ARTICLE_OUTPUT_DIR", "library/06_articles/wechat_official")
PROGRESS_FILE = os.environ.get("ARTICLE_PROGRESS_FILE", "workspace/capture/article_fetch_progress.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "captured": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def safe_filename(title, max_len=80):
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = re.sub(r'\s+', ' ', title).strip()
    if len(title) > max_len:
        title = title[:max_len]
    return title

def strip_html_tags(text):
    """移除HTML标签，保留文本"""
    # 替换块级标签为换行
    text = re.sub(r'<(p|div|br|h[1-6]|li|tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # 移除所有标签
    text = re.sub(r'<[^>]+>', '', text)
    # 处理HTML实体
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    # 清理多余空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def response(flow):
    # 只捕获文章详情页的响应
    url = flow.request.pretty_url
    if "mp.weixin.qq.com/s" not in url and "mp.weixin.qq.com/mp/appmsg" not in url:
        return

    # 跳过验证码页面
    if "captcha" in url:
        return

    # 只处理HTML响应
    content_type = flow.response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return

    html = flow.response.text
    if not html or len(html) < 1000:
        return

    # 检查是否包含正文
    if "js_content" not in html and "rich_media_content" not in html:
        return

    # 用正则提取标题
    title_match = re.search(r'<h1[^>]*id="activity-name"[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = strip_html_tags(title_match.group(1)) if title_match else "无标题"

    # 作者
    author_match = re.search(r'<span[^>]*class="rich_media_meta[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    author = strip_html_tags(author_match.group(1)) if author_match else ""

    # 发布时间
    time_match = re.search(r'<em[^>]*id="publish_time"[^>]*>(.*?)</em>', html, re.DOTALL)
    pub_time = strip_html_tags(time_match.group(1)) if time_match else ""

    # 正文
    content_match = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
    if not content_match:
        content_match = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not content_match:
        return

    content_html = content_match.group(1)
    content = strip_html_tags(content_html)

    # 图片
    images = re.findall(r'<img[^>]*data-src="([^"]+)"', content_html)
    if not images:
        images = re.findall(r'<img[^>]*src="(https?://[^"]+)"', content_html)

    # 日期
    date_str = pub_time[:10] if pub_time else datetime.now().strftime('%Y-%m-%d')

    # 保存文章
    filename = f"{date_str}_{safe_filename(title)}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    md_content = f"""# {title}

> 作者：{author}
> 发布时间：{pub_time}
> 原文链接：{url}
> 抓取时间：{datetime.now().isoformat()}

---

{content}

---

## 图片链接（{len(images)}张）

"""
    for i, img_url in enumerate(images, 1):
        md_content += f"{i}. {img_url}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 更新进度
    progress = load_progress()
    if url not in progress["completed"]:
        progress["completed"].append(url)
        progress["captured"].append({
            "title": title,
            "url": url,
            "date": date_str,
            "file": filename,
            "images": len(images),
            "content_length": len(content),
            "captured_at": datetime.now().isoformat(),
        })
        save_progress(progress)

    print(f"[CAPTURED] [{date_str}] {title[:40]} ({len(content)}字, {len(images)}图)")
    print(f"           保存: {filename}")
