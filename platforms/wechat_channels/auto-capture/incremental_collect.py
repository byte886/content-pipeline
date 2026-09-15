#!/usr/bin/env python3
"""
增量采集工具 - 只采集和下载新视频

功能：
1. 维护已采集视频清单（按视频ID去重）
2. 对比新捕获的视频列表，只返回新增视频
3. 自动更新清单
4. 支持按视频号分组管理

用法：
    # 初始化清单（首次全量采集后运行）
    python3 incremental_collect.py init --manifest manifest.json --videos videos.json
    
    # 检查新增视频
    python3 incremental_collect.py check --manifest manifest.json --videos new_videos.json
    
    # 采集并下载新增视频
    python3 incremental_collect.py collect --manifest manifest.json --videos new_videos.json --output-dir ./downloads
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


class IncrementalCollector:
    """增量采集器"""

    def __init__(self, manifest_path):
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        """加载已采集清单"""
        if self.manifest_path.exists():
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'channels': {},
            'total_videos': 0
        }

    def _save_manifest(self):
        """保存清单"""
        self.manifest['updated_at'] = datetime.now().isoformat()
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def init(self, videos, channel_name='default'):
        """初始化清单（首次全量采集）"""
        if channel_name not in self.manifest['channels']:
            self.manifest['channels'][channel_name] = {
                'name': channel_name,
                'video_ids': [],
                'videos': {},
                'last_collect_at': datetime.now().isoformat(),
                'total_collected': 0
            }

        channel = self.manifest['channels'][channel_name]
        added = 0

        for video in videos:
            video_id = video.get('id', '')
            if not video_id:
                # 用URL作为ID
                video_id = video.get('url', '')[:100]

            if video_id not in channel['videos']:
                channel['videos'][video_id] = {
                    'id': video_id,
                    'url': video.get('url', ''),
                    'description': video.get('description', ''),
                    'decode_key': video.get('decode_key', ''),
                    'size': video.get('size', 0),
                    'collected_at': datetime.now().isoformat(),
                    'downloaded': False
                }
                channel['video_ids'].append(video_id)
                added += 1

        channel['total_collected'] = len(channel['videos'])
        channel['last_collect_at'] = datetime.now().isoformat()
        self.manifest['total_videos'] = sum(
            ch['total_collected'] for ch in self.manifest['channels'].values()
        )
        self._save_manifest()

        return {
            'added': added,
            'total': len(channel['videos']),
            'channel': channel_name
        }

    def check_new(self, videos, channel_name='default'):
        """检查新增视频"""
        if channel_name not in self.manifest['channels']:
            # 新频道，全部都是新的
            return videos

        channel = self.manifest['channels'][channel_name]
        existing_ids = set(channel['videos'].keys())
        new_videos = []

        for video in videos:
            video_id = video.get('id', '')
            if not video_id:
                video_id = video.get('url', '')[:100]

            if video_id not in existing_ids:
                new_videos.append(video)

        return new_videos

    def collect(self, videos, channel_name='default', mark_downloaded=True):
        """采集新增视频并更新清单"""
        new_videos = self.check_new(videos, channel_name)

        if not new_videos:
            return {
                'new_count': 0,
                'total': self.manifest['channels'].get(channel_name, {}).get('total_collected', 0),
                'videos': []
            }

        # 添加到清单
        if channel_name not in self.manifest['channels']:
            self.manifest['channels'][channel_name] = {
                'name': channel_name,
                'video_ids': [],
                'videos': {},
                'last_collect_at': datetime.now().isoformat(),
                'total_collected': 0
            }

        channel = self.manifest['channels'][channel_name]

        for video in new_videos:
            video_id = video.get('id', '')
            if not video_id:
                video_id = video.get('url', '')[:100]

            channel['videos'][video_id] = {
                'id': video_id,
                'url': video.get('url', ''),
                'description': video.get('description', ''),
                'decode_key': video.get('decode_key', ''),
                'size': video.get('size', 0),
                'collected_at': datetime.now().isoformat(),
                'downloaded': mark_downloaded
            }
            channel['video_ids'].append(video_id)

        channel['total_collected'] = len(channel['videos'])
        channel['last_collect_at'] = datetime.now().isoformat()
        self.manifest['total_videos'] = sum(
            ch['total_collected'] for ch in self.manifest['channels'].values()
        )
        self._save_manifest()

        return {
            'new_count': len(new_videos),
            'total': len(channel['videos']),
            'videos': new_videos,
            'channel': channel_name
        }

    def get_stats(self):
        """获取统计信息"""
        stats = {
            'total_videos': self.manifest['total_videos'],
            'channels': {},
            'created_at': self.manifest['created_at'],
            'updated_at': self.manifest['updated_at']
        }

        for name, channel in self.manifest['channels'].items():
            stats['channels'][name] = {
                'total': channel['total_collected'],
                'last_collect': channel['last_collect_at'],
                'downloaded': sum(
                    1 for v in channel['videos'].values() if v.get('downloaded')
                )
            }

        return stats


def load_videos(filepath):
    """加载视频列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='增量采集工具')
    parser.add_argument('action', choices=['init', 'check', 'collect', 'stats'],
                        help='操作类型')
    parser.add_argument('--manifest', required=True, help='清单文件路径')
    parser.add_argument('--videos', help='视频列表JSON文件')
    parser.add_argument('--channel', default='default', help='视频号名称')
    parser.add_argument('--output', help='新增视频输出文件')
    args = parser.parse_args()

    collector = IncrementalCollector(args.manifest)

    if args.action == 'init':
        if not args.videos:
            print('错误: init需要--videos参数')
            sys.exit(1)
        videos = load_videos(args.videos)
        result = collector.init(videos, args.channel)
        print(f"初始化完成!")
        print(f"  视频号: {result['channel']}")
        print(f"  新增: {result['added']}")
        print(f"  总计: {result['total']}")

    elif args.action == 'check':
        if not args.videos:
            print('错误: check需要--videos参数')
            sys.exit(1)
        videos = load_videos(args.videos)
        new_videos = collector.check_new(videos, args.channel)
        print(f"检查完成!")
        print(f"  输入视频数: {len(videos)}")
        print(f"  新增视频数: {len(new_videos)}")

        if new_videos and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(new_videos, f, ensure_ascii=False, indent=2)
            print(f"  新增视频已保存到: {args.output}")

        if new_videos:
            print("\n新增视频列表:")
            for i, v in enumerate(new_videos[:10], 1):
                print(f"  {i}. {v.get('description', '无标题')[:50]}")
            if len(new_videos) > 10:
                print(f"  ... 还有 {len(new_videos) - 10} 个")

    elif args.action == 'collect':
        if not args.videos:
            print('错误: collect需要--videos参数')
            sys.exit(1)
        videos = load_videos(args.videos)
        result = collector.collect(videos, args.channel)
        print(f"采集完成!")
        print(f"  视频号: {result.get('channel', args.channel)}")
        print(f"  新增: {result['new_count']}")
        print(f"  总计: {result['total']}")

        if result['videos'] and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result['videos'], f, ensure_ascii=False, indent=2)
            print(f"  新增视频已保存到: {args.output}")

    elif args.action == 'stats':
        stats = collector.get_stats()
        print(f"=== 采集统计 ===")
        print(f"总视频数: {stats['total_videos']}")
        print(f"创建时间: {stats['created_at']}")
        print(f"更新时间: {stats['updated_at']}")
        print(f"\n各视频号:")
        for name, ch_stats in stats['channels'].items():
            print(f"  {name}:")
            print(f"    总数: {ch_stats['total']}")
            print(f"    已下载: {ch_stats['downloaded']}")
            print(f"    上次采集: {ch_stats['last_collect']}")


if __name__ == '__main__':
    main()
