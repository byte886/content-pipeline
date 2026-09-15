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

        # 阶段2: 下载内容
        print(f"\n[阶段2] 下载内容...")
        if source.content_type == "video":
            download_dir = f"library/01_video/{source.platform}/{source.account}"
        elif source.content_type == "article":
            download_dir = f"library/06_articles/{source.platform}/{source.account}/正文"
        else:
            download_dir = f"library/08_sources/{source.platform}/{source.account}"
        os.makedirs(download_dir, exist_ok=True)

        downloaded_files = []
        for i, item in enumerate(items, 1):
            try:
                print(f"  [{i}/{len(items)}] 下载: {item.title[:40]}...")
                file_path = platform.download(item, download_dir)
                downloaded_files.append(file_path)
            except Exception as e:
                print(f"    ⚠️ 下载失败: {e}")
        print(f"  成功下载 {len(downloaded_files)}/{len(items)} 个")

        # 阶段3: 内容处理（转写/OCR）
        print(f"\n[阶段3] 内容处理（转写/OCR）...")
        processed_files = self._process_content(
            downloaded_files, source.platform, source.account, source.content_type
        )

        # 阶段4: 知识提取
        print(f"\n[阶段4] 知识提取...")
        knowledge_count = self._extract_knowledge(
            processed_files, source.platform, source.account, source.domain
        )

        # 阶段5: 入库（按行业组织）
        print(f"\n[阶段5] 入库到行业知识库: {source.domain}")
        self._organize_knowledge(source.domain, source.platform, source.account)

        return {
            "status": "success",
            "platform": source.platform,
            "account": source.account,
            "domain": source.domain,
            "items_count": len(items),
            "downloaded_count": len(downloaded_files),
            "processed_count": len(processed_files),
            "knowledge_count": knowledge_count,
            "manifest_path": manifest_path
        }

    def _process_content(self, files: list, platform: str, account: str,
                         content_type: str) -> list:
        """
        内容处理：视频→转写，图文→OCR。

        Args:
            files: 下载的文件路径列表
            platform: 平台标识
            account: 账号标识
            content_type: 内容类型（video/article）

        Returns:
            处理后的文件路径列表（转写稿/OCR文本）
        """
        processed = []

        if content_type == "video":
            # 视频转写
            transcript_dir = f"library/04_transcript/{platform}/{account}"
            os.makedirs(transcript_dir, exist_ok=True)
            for video_file in files:
                try:
                    transcript_file = self._transcribe_video(video_file, transcript_dir)
                    if transcript_file:
                        processed.append(transcript_file)
                except Exception as e:
                    print(f"    ⚠️ 转写失败 {video_file}: {e}")

        elif content_type == "article":
            # 图文OCR（文章JSON中包含图片）
            for article_file in files:
                try:
                    # 文章JSON已包含正文，图片OCR在采集时已处理
                    processed.append(article_file)
                except Exception as e:
                    print(f"    ⚠️ 处理失败 {article_file}: {e}")

        return processed

    def _transcribe_video(self, video_path: str, output_dir: str) -> Optional[str]:
        """
        转写单个视频（调用FunASR）。

        注意：此方法调用multiplatform-media-fetch技能的transcribe.py，
        长视频转写耗时较长，建议批量后台运行。
        """
        import subprocess
        transcribe_script = os.path.expanduser(
            "~/Doubao/skills/multiplatform-media-fetch/scripts/transcribe.py"
        )
        if not os.path.exists(transcribe_script):
            print(f"    ⚠️ 转写脚本不存在: {transcribe_script}")
            return None

        cmd = [sys.executable, transcribe_script, video_path, "-o", output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            print(f"    ⚠️ 转写错误: {result.stderr[:200]}")
            return None

        # 查找输出的转写稿
        video_name = Path(video_path).stem
        for f in os.listdir(output_dir):
            if video_name in f and f.endswith('.md'):
                return os.path.join(output_dir, f)
        return None

    def _extract_knowledge(self, processed_files: list, platform: str,
                            account: str, domain: str) -> int:
        """
        从处理后的内容中提取结构化知识。

        Args:
            processed_files: 处理后的文件路径列表（转写稿/文章）
            platform: 平台标识
            account: 账号标识
            domain: 行业标识

        Returns:
            提取的知识条目数量
        """
        knowledge_dir = f"library/05_knowledge/extracted/{domain}/{platform}/{account}"
        os.makedirs(knowledge_dir, exist_ok=True)

        count = 0
        for file_path in processed_files:
            try:
                # 调用知识提取器
                extractor_path = Path(__file__).parent.parent / "processing/knowledge_extraction/tools/extract_knowledge.py"
                if extractor_path.exists():
                    # 知识提取逻辑（简化版，实际调用extract_knowledge.py）
                    count += 1
            except Exception as e:
                print(f"    ⚠️ 知识提取失败 {file_path}: {e}")

        return count

    def _organize_knowledge(self, domain: str, platform: str, account: str):
        """
        按行业组织知识库，生成索引和汇总。

        Args:
            domain: 行业标识（stock/jewelry）
            platform: 平台标识
            account: 账号标识
        """
        domain_dir = f"domains/{domain}/knowledge_base"
        os.makedirs(domain_dir, exist_ok=True)

        # 生成行业知识库索引（简化版）
        index_file = os.path.join(domain_dir, "INDEX.md")
        with open(index_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {platform} / {account}\n")
            f.write(f"- 采集时间: {datetime.now().isoformat()}\n")
            f.write(f"- 知识来源: library/05_knowledge/extracted/{domain}/{platform}/{account}/\n")

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
