"""
平台采集基类（Platform Base）

所有平台采集插件必须实现此接口，主流程不关心具体平台，只调用接口。
新平台接入只需实现此接口，不改主流程。

设计参考：珠宝项目的08_sources平台无关外部源设计 + 多平台插件化架构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ContentItem:
    """统一的内容项数据结构（所有平台采集后都标准化为此格式）"""
    item_id: str           # 平台内唯一ID（如BV号、视频号ID、文章ID）
    title: str             # 标题
    url: str               # 原始URL
    content_type: str      # video / article / live / image
    platform: str          # 平台标识（wechat_channels / bilibili / douyin / youtube）
    author: str            # 作者/账号名
    published_at: Optional[str] = None  # 发布时间
    duration: Optional[int] = None      # 时长（秒，视频类）
    metadata: Optional[dict] = None     # 平台特有元数据（如DecodeKey、清晰度等）


class PlatformFetcher(ABC):
    """平台采集插件基类"""

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """平台唯一标识，如 'wechat_channels'、'bilibili'"""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台显示名称，如 '微信视频号'、'哔哩哔哩'"""
        pass

    @abstractmethod
    def fetch_urls(self, account: str, **kwargs) -> List[ContentItem]:
        """
        采集指定账号的全部内容URL清单。

        Args:
            account: 账号标识（如公众号名、视频号名、B站UID、抖音ID）
            **kwargs: 平台特有参数（如是否需要登录、代理设置等）

        Returns:
            内容项列表
        """
        pass

    @abstractmethod
    def download(self, item: ContentItem, output_dir: str, **kwargs) -> str:
        """
        下载单个内容项到指定目录。

        Args:
            item: 内容项（来自fetch_urls的结果）
            output_dir: 输出目录
            **kwargs: 平台特有参数（如清晰度、是否解密等）

        Returns:
            下载后的文件路径
        """
        pass

    def get_metadata(self, item: ContentItem) -> dict:
        """
        获取内容项的元数据（可选实现，默认返回item.metadata）。
        如播放量、点赞数、评论数等。
        """
        return item.metadata or {}

    def needs_authentication(self) -> bool:
        """是否需要登录认证（默认False）"""
        return False

    def get_watermark(self) -> dict:
        """
        获取增量采集的水位（watermark）。
        用于增量采集：上次采集到哪里，下次从哪里继续。
        """
        return {}

    def set_watermark(self, watermark: dict):
        """设置增量采集水位"""
        pass
