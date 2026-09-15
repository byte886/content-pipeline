#!/usr/bin/env python3
"""
知识库汇总与查询工具

功能：
1. 批量提取所有转写稿的知识
2. 生成知识库汇总（按主题/时间/标的分类）
3. 支持查询（按关键词、标签、标的、时间范围）

用法：
    # 批量提取知识
    python3 knowledge_base.py extract --transcripts data/transcripts --output data/knowledge

    # 生成汇总
    python3 knowledge_base.py summarize --knowledge-dir data/knowledge

    # 查询
    python3 knowledge_base.py query --keyword "反弹" --knowledge-dir data/knowledge
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 添加工具目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from extract_knowledge import KnowledgeExtractor


class KnowledgeBase:
    """知识库"""

    def __init__(self, knowledge_dir):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.data = []

    def load(self):
        """加载所有知识"""
        self.data = []
        for f in self.knowledge_dir.glob('*.json'):
            if f.name == 'knowledge_summary.json':
                continue
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    self.data.append(json.load(fp))
            except Exception as e:
                print(f"加载失败 {f}: {e}")
        print(f"加载 {len(self.data)} 条知识")

    def extract_all(self, transcripts_dir):
        """批量提取知识"""
        extractor = KnowledgeExtractor()

        # 查找所有转写稿
        transcript_files = []
        for root, dirs, files in os.walk(transcripts_dir):
            for f in files:
                if f == 'transcript.md':
                    transcript_files.append(os.path.join(root, f))

        print(f"找到 {len(transcript_files)} 个转写稿")

        for i, transcript_path in enumerate(transcript_files, 1):
            video_name = Path(transcript_path).parent.name
            output_file = self.knowledge_dir / f"{video_name}.json"

            if output_file.exists():
                print(f"[{i}/{len(transcript_files)}] 跳过: {video_name}")
                continue

            print(f"[{i}/{len(transcript_files)}] 提取: {video_name}")
            try:
                result = extractor.extract(transcript_path)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"  错误: {e}")

        # 重新加载
        self.load()
        self.save_summary()

    def save_summary(self):
        """保存汇总"""
        summary = {
            'total': len(self.data),
            'generated_at': datetime.now().isoformat(),
            'by_direction': defaultdict(int),
            'by_tags': defaultdict(int),
            'all_support_levels': [],
            'all_resistance_levels': [],
            'all_sectors': defaultdict(int),
            'all_stocks': [],
            'videos': []
        }

        for item in self.data:
            # 按方向统计
            direction = item.get('market_view', {}).get('direction', '未知')
            summary['by_direction'][direction] += 1

            # 按标签统计
            for tag in item.get('tags', []):
                summary['by_tags'][tag] += 1

            # 技术点位
            summary['all_support_levels'].extend(item.get('technical_levels', {}).get('support', []))
            summary['all_resistance_levels'].extend(item.get('technical_levels', {}).get('resistance', []))

            # 板块
            for sector in item.get('sector_opportunities', []):
                summary['all_sectors'][sector['name']] += 1

            # 个股
            summary['all_stocks'].extend(item.get('stock_mentions', []))

            # 视频列表
            summary['videos'].append({
                'id': item['video_id'],
                'title': item['title'],
                'direction': direction,
                'tags': item.get('tags', []),
                'summary': item.get('market_view', {}).get('summary', '')
            })

        # 转换为普通dict
        summary['by_direction'] = dict(summary['by_direction'])
        summary['by_tags'] = dict(summary['by_tags'])
        summary['all_sectors'] = dict(summary['all_sectors'])

        # 点位去重排序
        summary['all_support_levels'] = sorted(set(summary['all_support_levels']), key=int)
        summary['all_resistance_levels'] = sorted(set(summary['all_resistance_levels']), key=int)

        summary_file = self.knowledge_dir / 'knowledge_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n汇总已保存: {summary_file}")
        print(f"  总数: {summary['total']}")
        print(f"  看涨: {summary['by_direction'].get('看涨', 0)}")
        print(f"  看跌: {summary['by_direction'].get('看跌', 0)}")
        print(f"  震荡: {summary['by_direction'].get('震荡', 0)}")

        return summary

    def query(self, keyword=None, tag=None, direction=None, stock_code=None):
        """查询知识"""
        results = []

        for item in self.data:
            # 关键词搜索
            if keyword:
                text = json.dumps(item, ensure_ascii=False)
                if keyword not in text:
                    continue

            # 标签筛选
            if tag and tag not in item.get('tags', []):
                continue

            # 方向筛选
            if direction and item.get('market_view', {}).get('direction') != direction:
                continue

            # 个股筛选
            if stock_code:
                stocks = item.get('stock_mentions', [])
                if not any(s.get('code') == stock_code for s in stocks):
                    continue

            results.append(item)

        return results


def main():
    parser = argparse.ArgumentParser(description='知识库汇总与查询工具')
    parser.add_argument('action', choices=['extract', 'summarize', 'query'],
                        help='操作类型')
    parser.add_argument('--transcripts', default='data/transcripts', help='转写稿目录')
    parser.add_argument('--knowledge-dir', default='data/knowledge', help='知识库目录')
    parser.add_argument('--keyword', help='查询关键词')
    parser.add_argument('--tag', help='筛选标签')
    parser.add_argument('--direction', choices=['看涨', '看跌', '震荡'], help='筛选方向')
    parser.add_argument('--stock', help='筛选股票代码')
    args = parser.parse_args()

    kb = KnowledgeBase(args.knowledge_dir)

    if args.action == 'extract':
        kb.extract_all(args.transcripts)

    elif args.action == 'summarize':
        kb.load()
        kb.save_summary()

    elif args.action == 'query':
        kb.load()
        results = kb.query(
            keyword=args.keyword,
            tag=args.tag,
            direction=args.direction,
            stock_code=args.stock
        )
        print(f"找到 {len(results)} 条结果\n")
        for item in results[:20]:
            print(f"[{item['video_id']}] {item['title'][:50]}")
            print(f"  方向: {item['market_view']['direction']} | 标签: {', '.join(item['tags'][:5])}")
            print(f"  观点: {item['market_view']['summary'][:100]}")
            print()


if __name__ == '__main__':
    main()
