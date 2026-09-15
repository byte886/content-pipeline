"""
微信公众号采集插件（WeChat Official Account Fetcher）

实现PlatformFetcher接口，封装公众号文章采集逻辑。

注意：公众号采集需要微信登录态，通过微信内置浏览器访问文章。
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from platforms.base import PlatformFetcher, ContentItem


class WechatOfficialFetcher(PlatformFetcher):
    """微信公众号采集插件"""

    def __init__(self):
        self._project_root = Path(__file__).parent.parent.parent
        self._article_dir = self._project_root / "platforms/wechat_official/article"

    @property
    def platform_id(self) -> str:
        return "wechat_official"

    @property
    def platform_name(self) -> str:
        return "微信公众号"

    def fetch_urls(self, account: str, **kwargs) -> List[ContentItem]:
        """
        采集指定公众号的全部文章列表。

        注意：此方法需要人工干预！
        1. 在微信中搜索并打开公众号
        2. 进入"全部消息"或文章列表页面
        3. 滚动到底部加载所有文章
        4. 通过抓包或其他方式获取文章URL列表

        或者：如果已有文章URL清单文件，直接读取。

        Args:
            account: 公众号名称（如 "顶底之王"）
            **kwargs:
                - manifest_file: 已有文章清单JSON/CSV文件路径
                - articles_dir: 已有文章正文目录（从目录扫描）

        Returns:
            内容项列表
        """
        manifest_file = kwargs.get('manifest_file')
        articles_dir = kwargs.get('articles_dir')

        if manifest_file and os.path.exists(manifest_file):
            return self._parse_manifest(manifest_file, account)

        if articles_dir and os.path.exists(articles_dir):
            return self._scan_articles_dir(articles_dir, account)

        # 没有现成数据，需要人工采集
        print(f"请在微信中打开公众号「{account}」的文章列表页面")
        print("滚动到底部加载所有文章，然后将文章URL保存到清单文件")
        print(f"清单文件格式：JSON数组，每项包含 title、url、publish_time")
        return []

    def _parse_manifest(self, manifest_file: str, account: str) -> List[ContentItem]:
        """解析文章清单文件"""
        items = []
        ext = os.path.splitext(manifest_file)[1].lower()

        if ext == '.json':
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            articles = data if isinstance(data, list) else data.get('articles', [])
        elif ext == '.csv':
            import csv
            articles = []
            with open(manifest_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    articles.append(row)
        else:
            return []

        for i, a in enumerate(articles, 1):
            item = ContentItem(
                item_id=a.get('id', a.get('article_id', f'article_{i:03d}')),
                title=a.get('title', f'文章_{i:03d}'),
                url=a.get('url', a.get('link', '')),
                content_type="article",
                platform="wechat_official",
                author=account,
                published_at=a.get('publish_time', a.get('create_time', a.get('date', None))),
                metadata={
                    'digest': a.get('digest', a.get('summary', '')),
                    'cover': a.get('cover', a.get('pic', '')),
                    'author_name': a.get('author', ''),
                }
            )
            items.append(item)

        return items

    def _scan_articles_dir(self, articles_dir: str, account: str) -> List[ContentItem]:
        """从已有文章正文目录扫描"""
        items = []
        for filename in sorted(os.listdir(articles_dir)):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(articles_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                item = ContentItem(
                    item_id=data.get('id', filename.replace('.json', '')),
                    title=data.get('title', filename),
                    url=data.get('url', data.get('link', '')),
                    content_type="article",
                    platform="wechat_official",
                    author=account,
                    published_at=data.get('publish_time', data.get('date', None)),
                    metadata={
                        'local_path': filepath,
                        'has_content': bool(data.get('content', '')),
                        'image_count': len(data.get('images', [])),
                    }
                )
                items.append(item)
            except Exception:
                continue
        return items

    def download(self, item: ContentItem, output_dir: str, **kwargs) -> str:
        """
        下载/采集单篇公众号文章正文。

        注意：公众号文章需要通过微信内置浏览器访问，
        此方法假设文章URL可直接访问（已获取到mp.weixin.qq.com链接）。

        Args:
            item: 内容项
            output_dir: 输出目录
            **kwargs:
                - include_images: 是否下载文章图片（默认True）

        Returns:
            保存的文章JSON文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        url = item.url
        if not url:
            raise ValueError("内容项缺少URL")

        # 使用curl获取文章HTML
        html_path = os.path.join(output_dir, f"{item.item_id}.html")
        cmd = [
            'curl', '-L',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            '-o', html_path,
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"获取文章失败: {result.stderr}")

        # 解析文章内容
        article_data = self._parse_article_html(html_path, item)

        # 下载图片
        if kwargs.get('include_images', True) and article_data.get('images'):
            images_dir = os.path.join(output_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            for i, img_url in enumerate(article_data['images']):
                try:
                    img_path = os.path.join(images_dir, f"{item.item_id}_{i:03d}.jpg")
                    subprocess.run(
                        ['curl', '-L', '-o', img_path, img_url],
                        capture_output=True, timeout=30
                    )
                except Exception:
                    pass

        # 保存文章JSON
        output_path = os.path.join(output_dir, f"{item.item_id}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)

        # 清理临时HTML
        if os.path.exists(html_path):
            os.remove(html_path)

        return output_path

    def _parse_article_html(self, html_path: str, item: ContentItem) -> dict:
        """解析公众号文章HTML"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
        except Exception:
            return {
                'id': item.item_id,
                'title': item.title,
                'url': item.url,
                'content': '',
                'images': [],
                'publish_time': item.published_at,
            }

        # 提取标题
        title_match = re.search(r'<h1[^>]*class="rich_media_title"[^>]*>(.*?)</h1>', html, re.DOTALL)
        title = title_match.group(1).strip() if title_match else item.title

        # 提取正文
        content_match = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
        content_html = content_match.group(1) if content_match else ''

        # 简单去除HTML标签
        content_text = re.sub(r'<[^>]+>', '', content_html)
        content_text = re.sub(r'\s+', ' ', content_text).strip()

        # 提取图片
        images = re.findall(r'data-src="([^"]+)"', content_html)

        # 提取发布时间
        publish_match = re.search(r'var ct = "(\d+)"', html)
        publish_time = None
        if publish_match:
            publish_time = datetime.fromtimestamp(int(publish_match.group(1))).isoformat()

        return {
            'id': item.item_id,
            'title': title,
            'url': item.url,
            'content': content_text,
            'content_html': content_html,
            'images': images,
            'publish_time': publish_time or item.published_at,
            'author': item.author,
        }

    def needs_authentication(self) -> bool:
        """公众号需要微信登录态"""
        return True


# 工厂函数
def create_fetcher(**kwargs) -> WechatOfficialFetcher:
    """创建微信公众号采集插件实例"""
    return WechatOfficialFetcher(**kwargs)
