"""
B站采集插件（Bilibili Fetcher）

实现PlatformFetcher接口，复用bili_list.py的列表采集逻辑。
支持wbi签名通道（需登录态）和dynamic动态流通道（免登录）。
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# 添加当前目录到路径，以便导入bili_list
sys.path.insert(0, str(Path(__file__).parent))

from platforms.base import PlatformFetcher, ContentItem


class BilibiliFetcher(PlatformFetcher):
    """B站采集插件"""

    def __init__(self, cookie: str = None, use_dynamic: bool = True):
        """
        Args:
            cookie: B站登录Cookie（wbi通道需要）
            use_dynamic: 是否使用dynamic动态流通道（免登录，默认True）
        """
        self.cookie = cookie
        self.use_dynamic = use_dynamic
        self._bili_list = None

    @property
    def platform_id(self) -> str:
        return "bilibili"

    @property
    def platform_name(self) -> str:
        return "哔哩哔哩"

    def _get_bili_list(self):
        """延迟导入bili_list模块"""
        if self._bili_list is None:
            try:
                import bili_list
                self._bili_list = bili_list
            except ImportError:
                raise ImportError("bili_list.py 未找到，请确保在 platforms/bilibili/ 目录下")
        return self._bili_list

    def fetch_urls(self, account: str, **kwargs) -> List[ContentItem]:
        """
        采集指定UP主的全部视频列表。

        Args:
            account: UP主UID（数字字符串，如 "1841256325"）
            **kwargs:
                - use_dynamic: 覆盖默认通道选择
                - max_count: 最大采集数量（默认全部）

        Returns:
            内容项列表
        """
        use_dynamic = kwargs.get('use_dynamic', self.use_dynamic)
        max_count = kwargs.get('max_count', None)

        bili = self._get_bili_list()

        # 使用dynamic通道采集
        if use_dynamic:
            videos = bili.fetch_dynamic_videos(account, cookie=self.cookie)
        else:
            videos = bili.fetch_wbi_videos(account, cookie=self.cookie)

        # 限制数量
        if max_count:
            videos = videos[:max_count]

        # 转换为ContentItem
        items = []
        for v in videos:
            item = ContentItem(
                item_id=v.get('bvid', v.get('aid', '')),
                title=v.get('title', ''),
                url=f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                content_type="video",
                platform="bilibili",
                author=v.get('owner', {}).get('name', account),
                published_at=v.get('pubdate', v.get('ctime', None)),
                duration=v.get('duration', None),
                metadata={
                    'aid': v.get('aid'),
                    'bvid': v.get('bvid'),
                    'view': v.get('stat', {}).get('view'),
                    'like': v.get('stat', {}).get('like'),
                    'danmaku': v.get('stat', {}).get('danmaku'),
                    'pic': v.get('pic'),
                    'desc': v.get('desc', ''),
                }
            )
            items.append(item)

        return items

    def download(self, item: ContentItem, output_dir: str, **kwargs) -> str:
        """
        下载单个B站视频。

        Args:
            item: 内容项
            output_dir: 输出目录
            **kwargs:
                - quality: 清晰度（默认最高）
                - audio_only: 仅下载音频

        Returns:
            下载后的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        # 使用yt-dlp下载（B站支持最好）
        bvid = item.metadata.get('bvid', item.item_id)
        url = f"https://www.bilibili.com/video/{bvid}"

        output_template = os.path.join(output_dir, f"{item.item_id}_%(title)s.%(ext)s")

        cmd = [
            'yt-dlp',
            '-o', output_template,
            '--no-playlist',
        ]

        if kwargs.get('audio_only'):
            cmd.extend(['-x', '--audio-format', 'mp3'])

        if self.cookie:
            cmd.extend(['--cookie', self.cookie])

        cmd.append(url)

        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"下载失败: {result.stderr}")

        # 查找下载的文件
        for f in os.listdir(output_dir):
            if f.startswith(item.item_id):
                return os.path.join(output_dir, f)

        return output_dir

    def needs_authentication(self) -> bool:
        """wbi通道需要登录，dynamic通道不需要"""
        return not self.use_dynamic


# 工厂函数
def create_fetcher(**kwargs) -> BilibiliFetcher:
    """创建B站采集插件实例"""
    return BilibiliFetcher(**kwargs)
