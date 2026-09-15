#!/usr/bin/env python3
"""
内容标准化引擎
- 将各平台内容转换为统一的ContentItem格式
- 去重（基于URL/标题/内容哈希）
- 血缘追踪（记录来源和处理步骤）
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class ContentItem:
    """统一内容项格式"""
    id: str                    # 唯一ID（平台+原始ID）
    platform: str              # 平台：wechat_channels / wechat_official / bilibili / douyin / youtube
    source_account: str        # 来源账号
    content_type: str          # 类型：video / live / article / image
    title: str
    url: str
    publish_time: Optional[str] = None
    duration: Optional[int] = None  # 视频时长（秒）
    local_path: Optional[str] = None
    transcript_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    lineage: List[dict] = field(default_factory=list)  # 血缘追踪

    def add_lineage(self, step: str, detail: str = ""):
        """添加处理步骤到血缘追踪"""
        self.lineage.append({
            "step": step,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })

    def to_dict(self) -> dict:
        return asdict(self)


class ContentNormalizer:
    """内容标准化器"""

    def __init__(self, dedup_enabled: bool = True):
        self.dedup_enabled = dedup_enabled
        self.seen_ids = set()
        self.seen_hashes = set()

    def normalize(self, raw_item: dict, platform: str, source_account: str) -> ContentItem:
        """将原始采集项标准化为ContentItem"""
        # 生成唯一ID
        raw_id = raw_item.get('id') or raw_item.get('video_id') or raw_item.get('msgid', '')
        item_id = f"{platform}_{raw_id}" if raw_id else self._hash_id(raw_item.get('url', ''))

        item = ContentItem(
            id=item_id,
            platform=platform,
            source_account=source_account,
            content_type=raw_item.get('type', 'video'),
            title=raw_item.get('title', ''),
            url=raw_item.get('url', ''),
            publish_time=raw_item.get('publish_time'),
            duration=raw_item.get('duration'),
            local_path=raw_item.get('local_path'),
            tags=raw_item.get('tags', []),
            metadata={k: v for k, v in raw_item.items()
                      if k not in ('id', 'title', 'url', 'type', 'publish_time', 'duration', 'local_path', 'tags')}
        )
        item.add_lineage("normalize", f"从{platform}采集标准化")
        return item

    def is_duplicate(self, item: ContentItem) -> bool:
        """检查是否重复"""
        if not self.dedup_enabled:
            return False
        if item.id in self.seen_ids:
            return True
        content_hash = self._content_hash(item)
        if content_hash in self.seen_hashes:
            return True
        return False

    def register(self, item: ContentItem):
        """注册已处理项"""
        self.seen_ids.add(item.id)
        self.seen_hashes.add(self._content_hash(item))

    @staticmethod
    def _hash_id(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:12]

    @staticmethod
    def _content_hash(item: ContentItem) -> str:
        """基于标题+URL生成内容哈希（用于去重）"""
        content = f"{item.title}|{item.url}"
        return hashlib.md5(content.encode()).hexdigest()


def save_manifest(items: List[ContentItem], output_path: str):
    """保存内容清单到JSON"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)


def load_manifest(input_path: str) -> List[ContentItem]:
    """从JSON加载内容清单"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [ContentItem(**item) for item in data]
