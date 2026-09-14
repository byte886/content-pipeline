#!/usr/bin/env python3
"""
知识提取脚本 - 从视频转写稿中提取结构化知识

功能：
1. 读取转写稿（Markdown）
2. 提取市场观点、技术点位、板块机会、个股推荐、操作建议
3. 输出结构化JSON
4. 支持批量处理

数据结构：
{
    "video_id": "short_001",
    "title": "视频标题",
    "date": "2026-09-15",
    "market_view": {
        "direction": "看涨|看跌|震荡",
        "confidence": "高|中|低",
        "summary": "核心观点"
    },
    "technical_levels": {
        "support": ["3200", "3150"],
        "resistance": ["3275", "3350"]
    },
    "sector_opportunities": [
        {"name": "新能源", "logic": "超跌反弹"}
    ],
    "stock_mentions": [
        {"name": "贵州茅台", "code": "600519", "sentiment": "正面|负面|中性"}
    ],
    "trading_advice": {
        "position": "仓位建议",
        "action": "操作建议"
    },
    "key_quotes": ["金句1", "金句2"],
    "tags": ["A股", "反弹", "技术分析"]
}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime


class KnowledgeExtractor:
    """知识提取器"""

    def __init__(self):
        # 股票代码正则（6位数字）
        self.stock_code_pattern = re.compile(r'\b(\d{6})\b')
        # 关键点位正则（如3200点、3275、支撑位3150）
        self.point_pattern = re.compile(r'(\d{3,4})\s*点')
        # 支撑/压力位关键词
        self.support_keywords = ['支撑', '支撑位', '下档支撑', '下方支撑']
        self.resistance_keywords = ['压力', '压力位', '阻力', '阻力位', '上档压力', '上方压力']
        # 看涨/看跌关键词
        self.bullish_keywords = ['反弹', '上涨', '看涨', '看多', '突破', '拉升', '走强', '走高', '机会']
        self.bearish_keywords = ['下跌', '看跌', '看空', '破位', '走弱', '走低', '风险', '回调', '调整']

    def extract(self, transcript_path, video_id=None, title=None):
        """从转写稿提取知识"""
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取正文（去掉标题和元信息）
        body = self._extract_body(content)

        # 如果没有指定video_id，使用父目录名（因为transcribe.py输出在子目录中）
        if not video_id:
            parent_name = Path(transcript_path).parent.name
            if parent_name and parent_name != Path(transcript_path).stem:
                video_id = parent_name
            else:
                video_id = Path(transcript_path).stem

        result = {
            'video_id': video_id,
            'title': title or self._extract_title(content),
            'extracted_at': datetime.now().isoformat(),
            'transcript_length': len(body),
            'market_view': self._extract_market_view(body),
            'technical_levels': self._extract_technical_levels(body),
            'sector_opportunities': self._extract_sectors(body),
            'stock_mentions': self._extract_stocks(body),
            'trading_advice': self._extract_trading_advice(body),
            'key_quotes': self._extract_key_quotes(body),
            'tags': self._extract_tags(body)
        }

        return result

    def _extract_body(self, content):
        """提取正文"""
        lines = content.split('\n')
        body_lines = []
        in_body = False
        for line in lines:
            if line.startswith('## 第'):
                in_body = True
                continue
            if in_body and line.strip() and not line.startswith('>'):
                body_lines.append(line.strip())
        return ' '.join(body_lines)

    def _extract_title(self, content):
        """提取标题"""
        match = re.search(r'^# (.+)$', content, re.MULTILINE)
        return match.group(1) if match else ''

    def _extract_market_view(self, text):
        """提取市场观点"""
        bullish_count = sum(text.count(kw) for kw in self.bullish_keywords)
        bearish_count = sum(text.count(kw) for kw in self.bearish_keywords)

        if bullish_count > bearish_count * 1.5:
            direction = '看涨'
            confidence = '高' if bullish_count > bearish_count * 2 else '中'
        elif bearish_count > bullish_count * 1.5:
            direction = '看跌'
            confidence = '高' if bearish_count > bullish_count * 2 else '中'
        else:
            direction = '震荡'
            confidence = '中'

        # 提取核心观点（第一句或包含关键词的句子）
        sentences = re.split(r'[。！？]', text)
        summary = ''
        for sent in sentences:
            if any(kw in sent for kw in ['反弹', '上涨', '下跌', '震荡', '调整', '突破', '破位']):
                summary = sent.strip()
                break
        if not summary and sentences:
            summary = sentences[0].strip()

        return {
            'direction': direction,
            'confidence': confidence,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'summary': summary[:200]
        }

    def _extract_technical_levels(self, text):
        """提取技术点位"""
        support = []
        resistance = []

        sentences = re.split(r'[。！？，；]', text)
        for sent in sentences:
            points = self.point_pattern.findall(sent)
            if not points:
                continue
            # 判断是支撑还是压力
            if any(kw in sent for kw in self.support_keywords):
                support.extend(points)
            elif any(kw in sent for kw in self.resistance_keywords):
                resistance.extend(points)

        # 去重并排序
        support = sorted(set(support), key=int)
        resistance = sorted(set(resistance), key=int)

        return {
            'support': support,
            'resistance': resistance
        }

    def _extract_sectors(self, text):
        """提取板块机会"""
        # 常见板块关键词
        sector_keywords = [
            '新能源', '光伏', '锂电', '储能', '半导体', '芯片', 'AI', '人工智能',
            '医药', '医疗', '消费', '白酒', '食品', '军工', '券商', '银行', '保险',
            '地产', '房地产', '基建', '建材', '钢铁', '有色', '煤炭', '石油',
            '汽车', '新能源车', '智能驾驶', '机器人', '传媒', '游戏', '元宇宙',
            '农业', '养殖', '化工', '纺织', '服装', '家电', '家居', '旅游',
            '酒店', '航空', '机场', '航运', '港口', '公路', '铁路', '电力',
            '公用事业', '环保', '水务', '燃气', '通信', '5G', '云计算', '大数据',
            '数字经济', '信创', '国产替代', '中字头', '央企', '国企改革'
        ]

        sectors = []
        for kw in sector_keywords:
            if kw in text:
                # 找到包含该板块的句子，提取逻辑
                for sent in re.split(r'[。！？]', text):
                    if kw in sent:
                        sectors.append({
                            'name': kw,
                            'context': sent.strip()[:100]
                        })
                        break

        return sectors[:10]  # 最多10个

    def _extract_stocks(self, text):
        """提取个股提及"""
        stocks = []
        codes = self.stock_code_pattern.findall(text)

        for code in set(codes):
            # 判断情绪
            sentiment = '中性'
            for sent in re.split(r'[。！？，；]', text):
                if code in sent:
                    if any(kw in sent for kw in ['看好', '推荐', '机会', '上涨', '买入', '低吸']):
                        sentiment = '正面'
                    elif any(kw in sent for kw in ['风险', '下跌', '卖出', '回避', '谨慎']):
                        sentiment = '负面'
                    break

            stocks.append({
                'code': code,
                'name': '',  # 需要后续匹配
                'sentiment': sentiment
            })

        return stocks

    def _extract_trading_advice(self, text):
        """提取操作建议"""
        advice = {
            'position': '',
            'action': ''
        }

        # 仓位建议
        position_patterns = [
            r'(仓位|控仓|持仓).{0,20}(\d+%|\d+成|半仓|满仓|空仓|轻仓|重仓)',
            r'(\d+成|\d+%|半仓|满仓|空仓|轻仓|重仓).{0,10}(仓位|持仓)'
        ]
        for pattern in position_patterns:
            match = re.search(pattern, text)
            if match:
                advice['position'] = match.group(0)
                break

        # 操作建议
        action_keywords = ['持股', '持币', '买入', '卖出', '加仓', '减仓', '低吸', '高抛', '止损', '止盈']
        for kw in action_keywords:
            if kw in text:
                for sent in re.split(r'[。！？]', text):
                    if kw in sent:
                        advice['action'] = sent.strip()[:100]
                        break
                if advice['action']:
                    break

        return advice

    def _extract_key_quotes(self, text):
        """提取金句"""
        quotes = []
        sentences = re.split(r'[。！？]', text)

        for sent in sentences:
            sent = sent.strip()
            # 金句特征：包含比喻、对比、总结性词语
            if (len(sent) > 10 and len(sent) < 80 and
                any(kw in sent for kw in ['在于', '关键是', '核心是', '本质是', '记住', '切记', '永远', '不要', '必须'])):
                quotes.append(sent)

        return quotes[:5]

    def _extract_tags(self, text):
        """提取标签"""
        tags = []
        tag_keywords = {
            'A股': ['A股', '大盘', '沪指', '上证指数'],
            '反弹': ['反弹', '上涨', '拉升'],
            '调整': ['调整', '回调', '下跌'],
            '技术分析': ['支撑', '压力', '均线', 'MACD', 'KDJ', '形态'],
            '量能': ['放量', '缩量', '成交量', '量能'],
            '板块轮动': ['板块', '轮动', '热点'],
            '操作策略': ['仓位', '持股', '买入', '卖出'],
            '市场情绪': ['情绪', '人气', '恐慌', '贪婪']
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)

        return tags


def batch_extract(input_dir, output_dir):
    """批量提取知识"""
    extractor = KnowledgeExtractor()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有转写稿
    transcript_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f == 'transcript.md':
                transcript_files.append(os.path.join(root, f))

    print(f"找到 {len(transcript_files)} 个转写稿")

    results = []
    for i, transcript_path in enumerate(transcript_files, 1):
        print(f"[{i}/{len(transcript_files)}] 处理: {Path(transcript_path).parent.name}")

        try:
            result = extractor.extract(transcript_path)
            results.append(result)

            # 保存单个结果
            video_id = result['video_id']
            output_file = output_dir / f"{video_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"  错误: {e}")

    # 保存汇总
    summary_file = output_dir / 'knowledge_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(results),
            'extracted_at': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n提取完成!")
    print(f"  总数: {len(results)}")
    print(f"  输出: {output_dir}")
    print(f"  汇总: {summary_file}")

    return results


def main():
    parser = argparse.ArgumentParser(description='知识提取工具')
    parser.add_argument('input', help='输入目录或单个转写稿')
    parser.add_argument('--output', default='data/knowledge', help='输出目录')
    args = parser.parse_args()

    if os.path.isdir(args.input):
        batch_extract(args.input, args.output)
    else:
        extractor = KnowledgeExtractor()
        result = extractor.extract(args.input)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
