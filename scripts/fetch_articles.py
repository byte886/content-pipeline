#!/usr/bin/env python3
"""
公众号文章正文批量采集脚本
使用UA伪装法（微信内置浏览器标识），无需Cookie、无需登录、无需代理
"""

import json
import time
import random
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 配置
INPUT_FILE = "/Users/wenjiechen/Desktop/stock-knowledge-base/knowledge-base/02-公众号文章/文章URL列表.json"
OUTPUT_DIR = "/Users/wenjiechen/Desktop/stock-knowledge-base/knowledge-base/02-公众号文章/正文"
PROGRESS_FILE = "/Users/wenjiechen/Desktop/stock-knowledge-base/knowledge-base/02-公众号文章/采集进度.json"

# 微信内置浏览器UA（iPhone版）
UA_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN"

# Mac版微信UA（备用）
UA_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) MicroMessenger/8.0.0(0x18000000) NetType/WIFI Language/zh_CN"

HEADERS = {
    "User-Agent": UA_MOBILE,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

def load_articles():
    """加载文章URL列表"""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_progress():
    """加载采集进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "current_index": 0}

def save_progress(progress):
    """保存采集进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, '_')
    return name[:100]  # 限制长度

def fetch_article(url, max_retries=3):
    """获取单篇文章正文"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
            resp.encoding = 'utf-8'
            
            # 检查是否触发验证码
            if 'verify' in resp.url or '验证码' in resp.text[:1000]:
                print(f"  ⚠️  触发验证码，尝试 {attempt+1}/{max_retries}")
                time.sleep(5 * (attempt + 1))
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 提取标题
            title_elem = soup.find('h1', id='activity-name')
            title = title_elem.get_text(strip=True) if title_elem else '未命名'
            
            # 提取正文
            content_elem = soup.find('div', id='js_content')
            if not content_elem:
                print(f"  ⚠️  未找到正文容器，尝试 {attempt+1}/{max_retries}")
                time.sleep(3)
                continue
            
            # 移除script和style
            for tag in content_elem.find_all(['script', 'style']):
                tag.decompose()
            
            # 提取纯文本
            content_text = content_elem.get_text(separator='\n', strip=True)
            
            # 提取HTML（保留图片等格式）
            content_html = str(content_elem)
            
            # 提取发布时间
            publish_time = ''
            time_elem = soup.find('em', id='publish_time')
            if time_elem:
                publish_time = time_elem.get_text(strip=True)
            
            # 提取公众号名称
            author = ''
            author_elem = soup.find('a', id='js_name')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            # 提取文章中的图片URL
            images = []
            for img in content_elem.find_all('img'):
                src = img.get('data-src') or img.get('src')
                if src:
                    images.append(src)
            
            return {
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "url": url,
                "content_text": content_text,
                "content_html": content_html,
                "images": images,
                "image_count": len(images),
                "content_length": len(content_text),
            }
            
        except Exception as e:
            print(f"  ❌ 请求失败: {e}，尝试 {attempt+1}/{max_retries}")
            time.sleep(3 * (attempt + 1))
    
    return None

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载文章列表
    articles = load_articles()
    print(f"📚 共 {len(articles)} 篇文章待采集")
    
    # 加载进度
    progress = load_progress()
    completed_urls = set(progress["completed"])
    failed_urls = set(progress["failed"])
    
    print(f"✅ 已完成: {len(completed_urls)} 篇")
    print(f"❌ 已失败: {len(failed_urls)} 篇")
    print(f"⏳ 待采集: {len(articles) - len(completed_urls) - len(failed_urls)} 篇")
    print()
    
    # 采集
    success_count = 0
    fail_count = 0
    
    for i, article in enumerate(articles):
        url = article.get('url', '')
        title = article.get('title', '未命名')
        
        # 跳过已完成
        if url in completed_urls:
            continue
        
        # 跳过已失败（可选择重试）
        if url in failed_urls:
            continue
        
        print(f"[{i+1}/{len(articles)}] {title[:40]}...")
        
        # 采集
        result = fetch_article(url)
        
        if result and result["content_length"] > 0:
            # 保存文章
            filename = sanitize_filename(f"{i+1:03d}_{result['title']}")
            output_file = os.path.join(OUTPUT_DIR, f"{filename}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            completed_urls.add(url)
            success_count += 1
            print(f"  ✅ 成功 ({result['content_length']}字, {result['image_count']}图)")
        else:
            failed_urls.add(url)
            fail_count += 1
            print(f"  ❌ 失败")
        
        # 保存进度
        progress["completed"] = list(completed_urls)
        progress["failed"] = list(failed_urls)
        progress["current_index"] = i
        save_progress(progress)
        
        # 随机延迟，避免触发风控
        delay = random.uniform(2.0, 4.0)
        time.sleep(delay)
        
        # 每10篇打印一次汇总
        if (i + 1) % 10 == 0:
            print(f"\n📊 进度: {i+1}/{len(articles)}, 成功: {success_count}, 失败: {fail_count}\n")
    
    print(f"\n🎉 采集完成！")
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {fail_count} 篇")
    print(f"📁 输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
