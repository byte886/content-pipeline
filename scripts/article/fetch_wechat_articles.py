#!/usr/bin/env python3
"""微信公众号文章自动化采集脚本 - 搜狗微信搜索模式"""
import os, sys, json, time, re, requests
from bs4 import BeautifulSoup
from datetime import datetime

class WeChatArticleFetcher:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_sogou(self, keyword, page=1):
        url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}&page={page}"
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = []
            for item in soup.select('.news-list li'):
                title_elem = item.select_one('h3 a')
                if not title_elem: continue
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                if link.startswith('/'): link = 'https://weixin.sogou.com' + link
                account = item.select_one('.account').get_text(strip=True) if item.select_one('.account') else ''
                summary = item.select_one('.txt-info').get_text(strip=True) if item.select_one('.txt-info') else ''
                articles.append({'title': title, 'url': link, 'account': account, 'summary': summary})
            return articles
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def fetch_article(self, url):
        try:
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            resp.encoding = 'utf-8'
            if 'weixin.sogou.com' in resp.url:
                match = re.search(r"url\s*=\s*['\"]([^'\"]+)['\"]", resp.text)
                if match:
                    resp = self.session.get(match.group(1), timeout=15)
                    resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = (soup.select_one('#activity-name') or soup.select_one('h1'))
            title = title.get_text(strip=True) if title else '未知'
            author = (soup.select_one('#js_name') or soup.select_one('.rich_media_meta_nickname'))
            author = author.get_text(strip=True) if author else ''
            date = (soup.select_one('#publish_time') or soup.select_one('.rich_media_meta_list em'))
            date = date.get_text(strip=True) if date else ''
            content = soup.select_one('#js_content') or soup.select_one('.rich_media_content')
            content = content.get_text('\n', strip=True) if content else ''
            images = [img.get('data-src') or img.get('src','') for img in (content and content.select('img') or []) if img.get('data-src') or img.get('src')]
            return {'title': title, 'author': author, 'date': date, 'content': content, 'images': images, 'url': resp.url}
        except Exception as e:
            print(f"抓取失败: {e}")
            return None
    
    def save(self, article, category="市场分析"):
        safe_title = article['title'][:30].replace('/','_').replace('\\','_')
        date_str = article.get('date') or datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.output_dir, category, f"{date_str}_{safe_title}.md")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        md = f"""---
title: {article['title']}
date: {date_str}
source: 公众号-{article.get('author','顶底之王')}
author: {article.get('author','')}
type: {category}
tags: []
original_url: {article.get('url','')}
images: {len(article.get('images',[]))}张
---

## 文章摘要
{article.get('summary','')}

## 正文
{article.get('content','')}
"""
        with open(filepath, 'w', encoding='utf-8') as f: f.write(md)
        return filepath

def main():
    output = "/Users/wenjiechen/Doubao/chats/2026-09-11/new-chat/stock-knowledge-base/knowledge-base/02-公众号文章"
    fetcher = WeChatArticleFetcher(output)
    print("搜索搜狗微信: 顶底之王")
    articles = fetcher.search_sogou("顶底之王", page=1)
    print(f"找到 {len(articles)} 篇文章")
    for i, a in enumerate(articles[:10]):
        print(f"[{i+1}] {a['title'][:40]} | {a['account']}")
        if '顶底' in a.get('account','') or '顶底' in a.get('title',''):
            content = fetcher.fetch_article(a['url'])
            if content:
                content['summary'] = a['summary']
                path = fetcher.save(content)
                print(f"  已保存: {path}")
            time.sleep(2)

if __name__ == '__main__':
    main()
