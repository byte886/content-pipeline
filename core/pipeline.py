"""
流水线编排（Pipeline）

统一编排：采集 → 处理 → 知识提取 → 入库
主流程不关心具体平台，通过平台插件接口调用。

设计参考：珠宝项目的五层架构 + 股票项目的四阶段流水线
"""

import os
import json
from typing import List, Optional
from datetime import datetime

from platforms.base import PlatformFetcher, ContentItem
from core.config import ConfigManager, SourceConfig


class Pipeline:
    """内容处理流水线"""

    def __init__(self, config_path: str = "config/sources.json"):
        self.config = ConfigManager(config_path)
        self.platforms: dict = {}  # platform_id -> PlatformFetcher实例
        self._register_platforms()

    def _register_platforms(self):
        """注册所有平台插件（延迟导入，避免依赖问题）"""
        # 已实现：wechat_official, wechat_channels, bilibili
        # 待实现：douyin, youtube（目前只有单视频下载，无列表采集）
        pass

    def _get_platform(self, platform_id: str) -> Optional[PlatformFetcher]:
        """获取平台插件实例"""
        if platform_id not in self.platforms:
            # 动态导入平台插件
            try:
                if platform_id == "wechat_channels":
                    from platforms.wechat_channels.fetcher import WechatChannelsFetcher
                    self.platforms[platform_id] = WechatChannelsFetcher()
                elif platform_id == "wechat_official":
                    from platforms.wechat_official.fetcher import WechatOfficialFetcher
                    self.platforms[platform_id] = WechatOfficialFetcher()
                elif platform_id == "bilibili":
                    from platforms.bilibili.fetcher import BilibiliFetcher
                    self.platforms[platform_id] = BilibiliFetcher(use_dynamic=True)
                elif platform_id in ("douyin", "youtube"):
                    print(f"[INFO] 平台 {platform_id} 目前仅支持单视频下载，列表采集待实现")
                    return None
            except ImportError as e:
                print(f"[WARN] 平台 {platform_id} 插件导入失败: {e}")
                return None
        return self.platforms.get(platform_id)

    def run_source(self, source: SourceConfig) -> dict:
        """
        运行单个采集源的完整流水线。

        流程：采集URL → 下载 → 转写/OCR → 知识提取 → 入库
        """
        print(f"\n{'='*60}")
        print(f"开始处理: {source.platform} / {source.account} (行业: {source.domain})")
        print(f"{'='*60}")

        platform = self._get_platform(source.platform)
        if not platform:
            return {"status": "error", "error": f"平台 {source.platform} 未实现"}

        # 阶段1: 采集URL
        print(f"\n[阶段1] 采集URL清单...")
        items = platform.fetch_urls(source.account, **source.config)
        print(f"  采集到 {len(items)} 个内容项")

        # 保存清单到台账
        manifest_dir = f"library/00_manifest/{source.platform}"
        os.makedirs(manifest_dir, exist_ok=True)
        manifest_path = f"{manifest_dir}/{source.account}_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump([item.__dict__ for item in items], f, ensure_ascii=False, indent=2)

        # 阶段2: 下载（具体平台实现）
        print(f"\n[阶段2] 下载内容...")
        output_dir = f"library/01_video/{source.platform}/{source.account}"
        os.makedirs(output_dir, exist_ok=True)
        # 实际下载由平台插件的download方法处理
        # 这里只做框架，具体调用在平台插件中

        # 阶段3: 转写/OCR（公共处理层）
        print(f"\n[阶段3] 内容处理（转写/OCR）...")
        # 调用processing/下的公共工具

        # 阶段4: 知识提取
        print(f"\n[阶段4] 知识提取...")
        # 调用processing/knowledge_extraction/

        # 阶段5: 入库（按行业）
        print(f"\n[阶段5] 入库到行业知识库: {source.domain}")
        # 输出到domains/{domain}/knowledge_base/

        return {
            "status": "success",
            "platform": source.platform,
            "account": source.account,
            "domain": source.domain,
            "items_count": len(items),
            "manifest_path": manifest_path
        }

    def run_domain(self, domain: str) -> List[dict]:
        """运行指定行业的所有采集源"""
        sources = self.config.get_sources_by_domain(domain)
        print(f"\n行业 '{domain}' 有 {len(sources)} 个采集源")
        results = []
        for source in sources:
            result = self.run_source(source)
            results.append(result)
        return results

    def run_all(self) -> List[dict]:
        """运行所有启用的采集源"""
        results = []
        for source in self.config.sources:
            if source.enabled:
                result = self.run_source(source)
                results.append(result)
        return results

    def incremental_update(self, platform: str, account: str) -> dict:
        """
        增量更新：只采集水位之后的新内容。
        设计参考：珠宝项目的水位（watermark）机制
        """
        platform_inst = self._get_platform(platform)
        if not platform_inst:
            return {"status": "error", "error": f"平台 {platform} 未实现"}

        # 读取水位
        watermark = platform_inst.get_watermark()
        print(f"当前水位: {watermark}")

        # 采集新内容（水位之后的）
        # ...

        # 更新水位
        # platform_inst.set_watermark(new_watermark)

        return {"status": "success", "watermark": watermark}


if __name__ == "__main__":
    # 示例：运行所有采集源
    pipeline = Pipeline()
    results = pipeline.run_all()
    print(f"\n完成！共处理 {len(results)} 个采集源")
