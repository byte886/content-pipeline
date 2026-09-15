"""
配置管理（Config）

管理平台、账号、行业的映射关系，驱动流水线执行。
配置文件：config/sources.yaml（或JSON）

设计参考：珠宝项目的00_manifest/sources.json水位机制
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SourceConfig:
    """采集源配置"""
    platform: str              # 平台标识（wechat_official / wechat_channels / bilibili / douyin / youtube）
    account: str               # 账号标识（公众号名、视频号名、B站UID等）
    domain: str                # 所属行业（stock / jewelry / creative-methods）
    enabled: bool = True       # 是否启用
    config: Dict = field(default_factory=dict)  # 平台特有配置


@dataclass
class DomainConfig:
    """行业配置"""
    domain_id: str             # 行业标识（stock / jewelry）
    name: str                  # 行业名称
    knowledge_base_dir: str    # 知识库目录
    article_writer_dir: str    # 文章撰写模板目录
    article_reviewer_dir: str  # 文章审稿规则目录
    config: Dict = field(default_factory=dict)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/sources.json"):
        self.config_path = config_path
        self.sources: List[SourceConfig] = []
        self.domains: Dict[str, DomainConfig] = {}
        self._load()

    def _load(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for s in data.get('sources', []):
                self.sources.append(SourceConfig(**s))
            for d in data.get('domains', []):
                self.domains[d['domain_id']] = DomainConfig(**d)

    def save(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {
            'sources': [s.__dict__ for s in self.sources],
            'domains': [d.__dict__ for d in self.domains.values()]
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_sources_by_domain(self, domain: str) -> List[SourceConfig]:
        """按行业获取采集源"""
        return [s for s in self.sources if s.domain == domain and s.enabled]

    def get_sources_by_platform(self, platform: str) -> List[SourceConfig]:
        """按平台获取采集源"""
        return [s for s in self.sources if s.platform == platform and s.enabled]

    def add_source(self, platform: str, account: str, domain: str, **kwargs):
        """添加采集源"""
        source = SourceConfig(
            platform=platform,
            account=account,
            domain=domain,
            config=kwargs
        )
        self.sources.append(source)
        self.save()

    def get_domain(self, domain_id: str) -> Optional[DomainConfig]:
        """获取行业配置"""
        return self.domains.get(domain_id)


# 默认配置（首次运行时创建）
DEFAULT_CONFIG = {
    "sources": [
        {
            "platform": "wechat_official",
            "account": "顶底之王",
            "domain": "stock",
            "enabled": True,
            "config": {}
        },
        {
            "platform": "wechat_channels",
            "account": "交易的游戏",
            "domain": "stock",
            "enabled": True,
            "config": {}
        }
    ],
    "domains": [
        {
            "domain_id": "stock",
            "name": "股票投资",
            "knowledge_base_dir": "domains/stock/knowledge_base",
            "article_writer_dir": "domains/stock/article_writer",
            "article_reviewer_dir": "domains/stock/article_reviewer",
            "config": {}
        },
        {
            "domain_id": "jewelry",
            "name": "珠宝",
            "knowledge_base_dir": "domains/jewelry/knowledge_base",
            "article_writer_dir": "domains/jewelry/article_writer",
            "article_reviewer_dir": "domains/jewelry/article_reviewer",
            "config": {}
        }
    ]
}
