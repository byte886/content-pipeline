#!/usr/bin/env python3
"""
图文OCR批量处理脚本

功能：
1. 批量将图片/PDF转为文字（使用work-doc-extract技能）
2. 支持五层引擎选型（Vision → PP-StructureV3 → PaddleOCR-VL → Unlimited-OCR）
3. 输出Markdown格式
4. 支持断点续跑

依赖：
- work-doc-extract 技能的 extract_text.py

用法：
    python3 batch_ocr.py <输入目录> <输出目录> [选项]

选项：
    --engine auto      引擎选择（auto/vision/paddle/vlm）
    --force            强制重新处理
    --limit N          只处理前N个文件
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# work-doc-extract 技能路径
EXTRACT_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/extract_text.py"

# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
    '.docx', '.pptx', '.xlsx', '.csv'
}


def find_files(directory):
    """查找目录中的所有支持的文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, f))
    return sorted(files)


def ocr_file(file_path, output_dir, engine='auto'):
    """OCR单个文件"""
    file_name = Path(file_path).stem
    output_file = os.path.join(output_dir, f"{file_name}.md")

    # 检查是否已处理
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return {'status': 'skipped', 'output': output_file}

    print(f"  处理: {file_name}")
    start_time = time.time()

    try:
        # 调用 extract_text.py
        cmd = [
            sys.executable,
            EXTRACT_SCRIPT,
            file_path,
            '-o', output_dir
        ]

        if engine != 'auto':
            cmd.extend(['--engine', engine])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"    完成: {size/1024:.1f}KB, 耗时{elapsed:.1f}秒")
                return {'status': 'success', 'output': output_file, 'time': elapsed}
            else:
                print(f"    警告: 未找到输出文件")
                print(f"    stdout: {result.stdout[-200:]}")
                return {'status': 'no_output', 'stdout': result.stdout[-500:]}
        else:
            print(f"    失败: {result.stderr[-200:]}")
            return {'status': 'failed', 'error': result.stderr[-500:]}

    except subprocess.TimeoutExpired:
        print(f"    超时: 超过10分钟")
        return {'status': 'timeout'}
    except Exception as e:
        print(f"    错误: {e}")
        return {'status': 'error', 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='图文OCR批量处理')
    parser.add_argument('input_dir', help='输入目录（图片/PDF/文档）')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--engine', default='auto',
                        choices=['auto', 'vision', 'paddle', 'vlm'],
                        help='引擎选择（默认auto）')
    parser.add_argument('--force', action='store_true',
                        help='强制重新处理')
    parser.add_argument('--limit', type=int, default=0,
                        help='只处理前N个文件')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"错误: 输入目录不存在: {input_dir}")
        sys.exit(1)

    # 查找文件
    files = find_files(str(input_dir))
    print(f"找到 {len(files)} 个文件")

    if args.limit > 0:
        files = files[:args.limit]
        print(f"限制处理前 {args.limit} 个")

    # 统计
    stats = {
        'total': len(files),
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }

    # 处理日志
    log_file = output_dir / 'ocr_log.json'
    log_data = []

    print(f"\n开始OCR处理...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"引擎: {args.engine}")
    print("=" * 60)

    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {Path(file_path).name}")

        if args.force:
            file_name = Path(file_path).stem
            output_file = output_dir / f"{file_name}.md"
            if output_file.exists():
                output_file.unlink()

        result = ocr_file(file_path, str(output_dir), args.engine)
        result['file'] = file_path
        log_data.append(result)

        if result['status'] == 'success':
            stats['success'] += 1
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
        else:
            stats['failed'] += 1
            stats['errors'].append({
                'file': file_path,
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
    print("OCR处理完成!")
    print(f"  总数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  失败: {stats['failed']}")
    print(f"  日志: {log_file}")

    if stats['errors']:
        print(f"\n失败列表:")
        for err in stats['errors'][:10]:
            print(f"  - {Path(err['file']).name}: {err['status']}")


if __name__ == '__main__':
    main()
