#!/usr/bin/env python3
"""微信公众号文章自动化采集脚本
模式1: sogou_search - 搜狗微信搜索获取文章列表（元数据）
模式2: chrome_fetch - 用Chrome自动化抓取文章正文（处理跳转）
模式3: ui_auto - 微信UI自动化打开文章（待实现）
"""
import os, sys, json, time, re, requests
from bs4 import BeautifulSoup
from datetime import datetime

class WeChatArticleFetcher:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_sogou(self, keyword, max_pages=3):
        """搜狗微信搜索获取文章列表"""
        all_articles = []
        for page in range(1, max_pages+1):
            url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}&page={page}"
            try:
                resp = self.session.get(url, timeout=15)
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.select('.news-list li'):
                    title_elem = item.select_one('h3 a')
                    if not title_elem: continue
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    if link.startswith('/'): link = 'https://weixin.sogou.com' + link
                    account = item.select_one('.account').get_text(strip=True) if item.select_one('.account') else ''
                    summary = item.select_one('.txt-info').get_text(strip=True) if item.select_one('.txt-info') else ''
                    # 提取日期（搜狗用时间戳或相对时间）
                    date_elem = item.select_one('.s2 script')
                    date = ''
                    if date_elem:
                        match = re.search(r"timeConvert\('(\d+)'\)", date_elem.string or '')
                        if match:
                            date = datetime.fromtimestamp(int(match.group(1))).strftime('%Y-%m-%d')
                    all_articles.append({
                        'title': title, 'url': link, 'account': account,
                        'summary': summary, 'date': date, 'source': 'sogou'
                    })
                time.sleep(1)
            except Exception as e:
                print(f"第{page}页搜索失败: {e}")
        return all_articles
    
    def save_metadata(self, articles, filename="articles_metadata.json"):
        """保存文章元数据（待Chrome抓取正文）"""
        filepath = os.path.join(self.output_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        return filepath
    
    def save_article_markdown(self, article, category="市场分析"):
        """保存文章为Markdown（已有完整内容时）"""
        safe_title = article['title'][:30].replace('/','_').replace('\\','_').replace(':','_')
        date_str = article.get('date') or datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.output_dir, category, f"{date_str}_{safe_title}.md")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        md = f"""---
title: {article['title']}
date: {date_str}
source: 公众号-{article.get('account','顶底之王')}
author: {article.get('account','')}
type: {category}
tags: []
original_url: {article.get('url','')}
fetched_at: {datetime.now().isoformat()}
---

## 文章摘要
{article.get('summary','')}

## 正文
{article.get('content','（待Chrome抓取正文）')}
"""
        with open(filepath, 'w', encoding='utf-8') as f: f.write(md)
        return filepath

def main():
    output = "/Users/wenjiechen/Doubao/chats/2026-09-11/new-chat/stock-knowledge-base/knowledge-base/02-公众号文章"
    fetcher = WeChatArticleFetcher(output)
    
    print("=== 搜狗微信搜索: 顶底之王 ===")
    articles = fetcher.search_sogou("顶底之王", max_pages=3)
    print(f"共找到 {len(articles)} 篇文章")
    
    # 过滤顶底之王的文章
    target = [a for a in articles if '顶底' in a.get('account','') or '顶底' in a.get('title','')]
    print(f"其中顶底之王: {len(target)} 篇")
    
    # 保存元数据
    meta_path = fetcher.save_metadata(target, "顶底之王_文章列表.json")
    print(f"元数据已保存: {meta_path}")
    
    # 打印文章列表
    for i, a in enumerate(target):
        print(f"[{i+1}] {a.get('date','?')} | {a['title'][:40]}")
    
    print("\n下一步: 用Chrome自动化抓取文章正文（处理搜狗跳转）")

if __name__ == '__main__':
    main()
