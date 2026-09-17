#!/usr/bin/env python3
"""
通用增量采集框架 — 多平台内容增量发现与下载

设计原则：
- 平台无关：基类定义通用流程，各平台只实现"获取最新列表"和"唯一键提取"
- 对比/下载/更新manifest是通用逻辑
- 配置化：从 config/sources.json 读取博主信息

用法：
  python3 scripts/incremental/fetch_new.py --platform bilibili --account 宝石学家老许
  python3 scripts/incremental/fetch_new.py --platform wechat_channels --account 交易的游戏
  python3 scripts/incremental/fetch_new.py --all                    # 所有启用的源
  python3 scripts/incremental/fetch_new.py --platform bilibili --dry-run  # 只对比不下载

唯一键：
- B站: bvid
- 视频号: 标题+大小(MB)（历史数据无唯一ID，用组合键）
- 公众号: 文章URL(__biz+mid)
"""

import argparse
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
LIBRARY_DIR = PROJECT_DIR / "library"
SOURCES_FILE = PROJECT_DIR / "config" / "sources.json"


class IncrementalFetcher(ABC):
    """增量采集基类 — 通用流程，平台只实现列表获取和唯一键"""

    def __init__(self, account: str, domain: str, platform: str, config: dict = None):
        self.account = account
        self.domain = domain
        self.platform = platform
        self.config = config or {}
        self.manifest_path = self._get_manifest_path()

    def _get_manifest_path(self) -> Path:
        """获取博主的manifest路径（按内容类型）"""
        # 视频类平台的manifest在01_video下
        video_platforms = ['bilibili', 'wechat_channels', 'douyin', 'youtube']
        if self.platform in video_platforms:
            return LIBRARY_DIR / "01_video" / self.domain / self.account / "manifest.json"
        # 图文类平台的manifest在06_articles下
        article_platforms = ['wechat_official', 'xiaohongshu']
        if self.platform in article_platforms:
            return LIBRARY_DIR / "06_articles" / self.domain / self.account / "manifest.json"
        return LIBRARY_DIR / "01_video" / self.domain / self.account / "manifest.json"

    def load_manifest(self) -> List[Dict[str, Any]]:
        """加载已有manifest"""
        if self.manifest_path.exists():
            with open(self.manifest_path, encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_manifest(self, data: List[Dict[str, Any]]):
        """保存manifest"""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @abstractmethod
    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """获取博主最新内容列表（各平台实现）
        返回: [{'title': ..., 'unique_key': ..., 'url': ..., ...}, ...]
        """
        pass

    @abstractmethod
    def get_unique_key(self, item: Dict[str, Any]) -> str:
        """提取唯一标识符（各平台实现）"""
        pass

    @abstractmethod
    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """下载单个内容（各平台实现），返回本地路径或None"""
        pass

    def get_next_index(self, manifest: List[Dict[str, Any]], item_type: str = None) -> int:
        """获取下一个编号"""
        if not manifest:
            return 1
        indices = []
        for m in manifest:
            idx = m.get('index', 0)
            if item_type and m.get('type') != item_type:
                continue
            if isinstance(idx, int) and idx > 0:
                indices.append(idx)
        return max(indices) + 1 if indices else 1

    def diff(self, latest: List[Dict[str, Any]], manifest: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对比最新列表和manifest，找出新增项"""
        existing_keys = set()
        for m in manifest:
            key = self.get_unique_key(m)
            if key:
                existing_keys.add(key)

        new_items = []
        for item in latest:
            key = self.get_unique_key(item)
            if key and key not in existing_keys:
                new_items.append(item)
        return new_items

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """执行增量采集主流程"""
        print(f"\n{'='*60}")
        print(f" 增量采集: {self.platform} / {self.account} ({self.domain})")
        print(f"{'='*60}")

        # 1. 加载已有manifest
        manifest = self.load_manifest()
        print(f"已有内容: {len(manifest)} 条")

        # 2. 获取最新列表
        print("获取最新列表...")
        try:
            latest = self.fetch_latest_list()
        except Exception as e:
            print(f"❌ 获取列表失败: {e}")
            return {'platform': self.platform, 'account': self.account, 'error': str(e), 'new': 0}
        print(f"最新列表: {len(latest)} 条")

        # 3. 对比发现新增
        new_items = self.diff(latest, manifest)
        print(f"新增内容: {len(new_items)} 条")

        if dry_run:
            for i, item in enumerate(new_items, 1):
                print(f"  [{i}] {item.get('title', '无标题')[:50]}")
            return {'platform': self.platform, 'account': self.account, 'new': len(new_items), 'dry_run': True}

        if not new_items:
            print("✅ 无新增内容")
            return {'platform': self.platform, 'account': self.account, 'new': 0}

        # 4. 下载新增内容
        downloaded = 0
        failed = 0
        for i, item in enumerate(new_items, 1):
            title = item.get('title', '无标题')[:40]
            item_type = item.get('type', 'short')
            index = self.get_next_index(manifest, item_type)
            print(f"  [{i}/{len(new_items)}] 下载 #{index}: {title}...", end=' ')

            local_path = self.download_item(item, index)
            if local_path and local_path.exists():
                # 补充元数据
                item['index'] = index
                item['path'] = str(local_path.relative_to(PROJECT_DIR))
                item['platform'] = self.platform
                item['account'] = self.account
                item['domain'] = self.domain
                manifest.append(item)
                downloaded += 1
                print("✅")
            else:
                failed += 1
                print("❌")

        # 5. 更新manifest
        if downloaded > 0:
            self.save_manifest(manifest)
            print(f"manifest已更新: {len(manifest)} 条")

        print(f"\n完成: 新增{downloaded}个, 失败{failed}个")
        return {
            'platform': self.platform,
            'account': self.account,
            'total': len(manifest),
            'new': downloaded,
            'failed': failed
        }


# ============================================================
# 平台实现
# ============================================================

class BilibiliFetcher(IncrementalFetcher):
    """B站增量采集 — 复用bili_list.py的wbi签名获取UP主动态"""

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """调用bili_list.py获取UP主最新视频列表（只取最新一页）"""
        import subprocess
        import tempfile

        uid = self.config.get('uid', '')
        if not uid:
            raise ValueError("B站UID未配置")

        # 用临时目录存放输出
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / f"up_{uid}_videos.json"
            cmd = [
                sys.executable,
                str(PROJECT_DIR / "platforms" / "bilibili" / "bili_list.py"),
                "wbi", "--uid", uid, "--max-pages", "1"
            ]
            env = os.environ.copy()
            env['BILI_OUTPUT_DIR'] = tmpdir

            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=60, env=env, cwd=str(PROJECT_DIR))

            if not output_file.exists():
                raise Exception(f"bili_list.py执行失败: {result.stderr[-200:]}")

            with open(output_file, encoding='utf-8') as f:
                videos = json.load(f)

        result = []
        for v in videos:
            result.append({
                'bvid': v['bvid'],
                'title': v['title'],
                'url': v.get('url', f"https://www.bilibili.com/video/{v['bvid']}"),
                'created': v.get('created', 0),
                'length': v.get('length', ''),
                'play': v.get('play', 0),
                'type': 'video',
            })
        return result

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        return item.get('bvid', '')

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """调用B站下载脚本"""
        # 复用已有的B站下载逻辑
        bvid = item['bvid']
        title = item['title'].replace('/', '_').replace('\\', '_')[:50]
        filename = f"video_{index:03d}_{title} [{bvid}].mp4"
        output_dir = LIBRARY_DIR / "01_video" / self.domain / self.account
        output_path = output_dir / filename

        if output_path.exists():
            return output_path

        # 调用yt-dlp或B站下载脚本
        import subprocess
        try:
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '-o', str(output_path),
                item['url']
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and output_path.exists():
                return output_path
        except Exception as e:
            print(f"下载失败: {e}")
        return None


class WechatChannelsFetcher(IncrementalFetcher):
    """视频号增量采集 — 需要网络捕获列表（预留接口）

    视频号没有公开API，需要通过res-downloader等工具捕获列表页请求。
    当前实现：从指定的JSON文件读取最新列表（由网络捕获工具生成）。
    """

    def __init__(self, account: str, domain: str, platform: str, config: dict = None):
        super().__init__(account, domain, platform, config)
        self.list_file = self.config.get('list_file', '')  # 网络捕获的列表JSON

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """从网络捕获的JSON文件读取最新列表"""
        if not self.list_file or not Path(self.list_file).exists():
            raise Exception(
                f"视频号列表文件不存在: {self.list_file}\n"
                f"请先用res-downloader捕获视频号列表页，保存为JSON后指定 --list-file"
            )
        with open(self.list_file, encoding='utf-8') as f:
            data = json.load(f)
        # 假设格式是列表，每项含title/size等
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'list' in data:
            return data['list']
        return []

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        """视频号用标题+大小作为组合键"""
        title = item.get('title', '')
        size = item.get('size_mb', item.get('size', 0))
        return f"{title}|{size}"

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """视频号下载需要网络捕获，暂不自动实现"""
        print("视频号下载需手动捕获（参考SOP-wechat-channels-capture.md）")
        return None


class WechatOfficialFetcher(IncrementalFetcher):
    """公众号增量采集 — 预留接口"""

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("公众号增量采集待实现（需网络捕获文章列表）")

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        return item.get('url', item.get('title', ''))

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        raise NotImplementedError("公众号下载待实现")


# ============================================================
# 工厂和入口
# ============================================================

FETCHER_REGISTRY = {
    'bilibili': BilibiliFetcher,
    'wechat_channels': WechatChannelsFetcher,
    'wechat_official': WechatOfficialFetcher,
}


def load_sources() -> List[Dict[str, Any]]:
    """加载采集源配置"""
    with open(SOURCES_FILE, encoding='utf-8') as f:
        data = json.load(f)
    return [s for s in data.get('sources', []) if s.get('enabled', True)]


def get_fetcher(platform: str, account: str = None) -> Optional[IncrementalFetcher]:
    """根据平台和账号获取Fetcher实例"""
    sources = load_sources()
    for s in sources:
        if s['platform'] == platform and (account is None or s['account'] == account):
            fetcher_cls = FETCHER_REGISTRY.get(platform)
            if fetcher_cls:
                config = s.get('config', {}).copy()
                # 把顶层的uid等字段也放入config
                if 'uid' in s:
                    config['uid'] = s['uid']
                return fetcher_cls(
                    account=s['account'],
                    domain=s['domain'],
                    platform=platform,
                    config=config
                )
    return None


def main():
    parser = argparse.ArgumentParser(description='多平台增量采集')
    parser.add_argument('--platform', help='平台: bilibili/wechat_channels/wechat_official')
    parser.add_argument('--account', help='博主账号名（可选，默认该平台第一个启用的源）')
    parser.add_argument('--all', action='store_true', help='采集所有启用的源')
    parser.add_argument('--dry-run', action='store_true', help='只对比不下载')
    parser.add_argument('--list-file', help='视频号列表JSON文件路径（网络捕获生成）')
    args = parser.parse_args()

    results = []

    if args.all:
        for source in load_sources():
            fetcher = get_fetcher(source['platform'], source['account'])
            if fetcher:
                if args.list_file and source['platform'] == 'wechat_channels':
                    fetcher.list_file = args.list_file
                results.append(fetcher.run(dry_run=args.dry_run))
    elif args.platform:
        fetcher = get_fetcher(args.platform, args.account)
        if not fetcher:
            print(f"❌ 未找到平台 {args.platform} 的配置")
            sys.exit(1)
        if args.list_file:
            fetcher.list_file = args.list_file
        results.append(fetcher.run(dry_run=args.dry_run))
    else:
        parser.print_help()
        sys.exit(1)

    # 汇总
    print(f"\n{'='*60}")
    print(" 增量采集汇总")
    print(f"{'='*60}")
    for r in results:
        if 'error' in r:
            print(f"  ❌ {r['platform']}/{r['account']}: {r['error']}")
        else:
            print(f"  ✅ {r['platform']}/{r['account']}: 新增{r.get('new', 0)}个, 总计{r.get('total', '?')}个")


if __name__ == '__main__':
    main()
