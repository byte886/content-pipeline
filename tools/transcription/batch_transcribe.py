#!/usr/bin/env python3
"""
视频转文字批量处理脚本

功能：
1. 批量将视频转为文字稿（使用FunASR本地离线转写）
2. 支持断点续跑（跳过已转写的视频）
3. 自动提取音频后转写
4. 输出Markdown格式的文字稿

依赖：
- multiplatform-media-fetch 技能的 transcribe.py
- FunASR（自动寻找带FunASR的Python环境）

用法：
    python3 batch_transcribe.py <视频目录> <输出目录> [选项]

选项：
    --lang zh          语种（默认auto）
    --force            强制重新转写（跳过已存在的）
    --limit N          只处理前N个视频
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# multiplatform-media-fetch 技能路径
TRANSCRIBE_SCRIPT = "/Users/wenjiechen/Doubao/skills/multiplatform-media-fetch/scripts/transcribe.py"

# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm'}


def find_videos(directory):
    """查找目录中的所有视频文件"""
    videos = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if Path(f).suffix.lower() in VIDEO_EXTENSIONS:
                videos.append(os.path.join(root, f))
    return sorted(videos)


def transcribe_video(video_path, output_dir, lang='auto'):
    """转写单个视频"""
    video_name = Path(video_path).stem
    output_file = os.path.join(output_dir, f"{video_name}.md")

    # 检查是否已转写
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return {'status': 'skipped', 'output': output_file}

    print(f"  转写: {video_name}")
    start_time = time.time()

    try:
        # 调用 transcribe.py
        cmd = [
            sys.executable,
            TRANSCRIBE_SCRIPT,
            video_path,
            output_dir,
            '--lang', lang
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            # 检查输出文件
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"    完成: {size/1024:.1f}KB, 耗时{elapsed:.1f}秒")
                return {'status': 'success', 'output': output_file, 'time': elapsed}
            else:
                # 可能输出在其他位置
                print(f"    警告: 未找到输出文件 {output_file}")
                print(f"    stdout: {result.stdout[-200:]}")
                return {'status': 'no_output', 'stdout': result.stdout[-500:]}
        else:
            print(f"    失败: {result.stderr[-200:]}")
            return {'status': 'failed', 'error': result.stderr[-500:]}

    except subprocess.TimeoutExpired:
        print(f"    超时: 超过1小时")
        return {'status': 'timeout'}
    except Exception as e:
        print(f"    错误: {e}")
        return {'status': 'error', 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='视频转文字批量处理')
    parser.add_argument('video_dir', help='视频目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--lang', default='auto',
                        choices=['auto', 'zh', 'ja', 'en', 'ko', 'yue'],
                        help='语种（默认auto）')
    parser.add_argument('--force', action='store_true',
                        help='强制重新转写')
    parser.add_argument('--limit', type=int, default=0,
                        help='只处理前N个视频')
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_dir.exists():
        print(f"错误: 视频目录不存在: {video_dir}")
        sys.exit(1)

    # 查找视频
    videos = find_videos(str(video_dir))
    print(f"找到 {len(videos)} 个视频文件")

    if args.limit > 0:
        videos = videos[:args.limit]
        print(f"限制处理前 {args.limit} 个")

    if args.force:
        print("强制模式: 将重新转写所有视频")

    # 统计
    stats = {
        'total': len(videos),
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }

    # 处理日志
    log_file = output_dir / 'transcribe_log.json'
    log_data = []

    print(f"\n开始转写...")
    print(f"视频目录: {video_dir}")
    print(f"输出目录: {output_dir}")
    print(f"语种: {args.lang}")
    print("=" * 60)

    for i, video_path in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {Path(video_path).name}")

        if args.force:
            # 强制模式：删除已存在的输出
            video_name = Path(video_path).stem
            output_file = output_dir / f"{video_name}.md"
            if output_file.exists():
                output_file.unlink()

        result = transcribe_video(video_path, str(output_dir), args.lang)
        result['video'] = video_path
        log_data.append(result)

        if result['status'] == 'success':
            stats['success'] += 1
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
        else:
            stats['failed'] += 1
            stats['errors'].append({
                'video': video_path,
                'status': result['status'],
                'error': result.get('error', '')
            })

    # 保存日志
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'details': log_data
        }, f, ensure_ascii=False, indent=2)

    # 输出统计
    print("\n" + "=" * 60)
    print("转写完成!")
    print(f"  总数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  失败: {stats['failed']}")
    print(f"  日志: {log_file}")

    if stats['errors']:
        print(f"\n失败列表:")
        for err in stats['errors'][:10]:
            print(f"  - {Path(err['video']).name}: {err['status']}")


if __name__ == '__main__':
    main()
