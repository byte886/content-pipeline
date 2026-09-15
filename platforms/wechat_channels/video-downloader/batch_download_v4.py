#!/usr/bin/env python3
"""
微信视频号批量下载脚本 v4
- 使用原始URL下载（稳定）
- 支持XOR解密（调用Node.js解密脚本）
- 支持去重和命名
- 修复文件名清理
"""
import json
import os
import re
import subprocess
import sys
import time

def download_video(url, output, max_retries=3, quality='default'):
    """下载视频
    quality: default(默认), max(最大xWT111), min(最小xWT128)
    """
    # 根据质量参数修改URL
    if quality == 'max' and 'X-snsvideoflag' not in url:
        url += '&X-snsvideoflag=xWT111'
    elif quality == 'min' and 'X-snsvideoflag' not in url:
        url += '&X-snsvideoflag=xWT128'
    
    for attempt in range(max_retries):
        cmd = [
            'curl', '-L', '-s', '-o', output,
            '-H', 'Referer: https://channels.weixin.qq.com/',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            '--connect-timeout', '30',
            '--max-time', '600',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and os.path.exists(output) and os.path.getsize(output) > 1000:
            return True
        time.sleep(2)
    return False

def decrypt_video(filepath, decode_key):
    """解密视频"""
    if not decode_key:
        return True
    
    cmd = ['node', '/tmp/wechat_decrypt.js', decode_key, filepath]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0

def verify_mp4(filepath):
    """验证是否为有效MP4"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(32)
        return header[4:8] == b'ftyp'
    except:
        return False

def sanitize_filename(name):
    """清理文件名"""
    # 移除换行符和控制字符
    name = re.sub(r'[\r\n\t]', '', name)
    # 替换非法字符
    name = re.sub(r'[/\\:*?"<>|#]', '_', name)
    # 替换多个空格为单个下划线
    name = re.sub(r'\s+', '_', name)
    # 移除首尾的下划线和点
    name = name.strip('_.')
    # 限制长度
    if len(name) > 60:
        name = name[:60]
    return name if name else 'untitled'

def main():
    if len(sys.argv) < 4:
        print("用法: python3 batch_download_v4.py <json文件> <输出目录> <类型:live/short> [起始序号] [质量:default/max/min]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_dir = sys.argv[2]
    video_type = sys.argv[3]
    start_idx = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    quality = sys.argv[5] if len(sys.argv) > 5 else 'default'
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(json_file, encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"开始下载 {len(videos)} 个视频到 {output_dir}")
    print(f"类型: {video_type}, 起始序号: {start_idx}")
    
    results = []
    for i, v in enumerate(videos):
        idx = start_idx + i
        title = v.get('description', f'video_{idx}')
        decode_key = v.get('decode_key', '')
        expected_size = v.get('size', 0)
        url = v.get('url', '')
        
        if not url:
            print(f"[{idx}/{len(videos)}] 跳过: 无URL")
            results.append({'idx': idx, 'title': title, 'status': 'no_url'})
            continue
        
        safe_title = sanitize_filename(title)
        output = os.path.join(output_dir, f"{video_type}_{idx:03d}_{safe_title}.mp4")
        
        # 跳过已存在且有效的文件
        if os.path.exists(output) and verify_mp4(output):
            print(f"[{idx}/{len(videos)}] 已存在，跳过: {title[:30]}")
            results.append({'idx': idx, 'title': title, 'status': 'skipped', 'size': os.path.getsize(output)})
            continue
        
        print(f"\n[{idx}/{len(videos)}] 下载: {title[:40]} ({expected_size/1024/1024:.1f}MB) [质量:{quality}]")
        print(f"  DecodeKey: {decode_key or '无'}")
        
        # 使用原始URL下载
        success = download_video(url, output, quality=quality)
        
        if success:
            actual_size = os.path.getsize(output)
            print(f"  下载完成: {actual_size/1024/1024:.1f}MB")
            
            # 解密
            if decode_key:
                print(f"  解密中...")
                decrypt_success = decrypt_video(output, decode_key)
                if decrypt_success and verify_mp4(output):
                    print(f"  ✓ 解密成功")
                    results.append({'idx': idx, 'title': title, 'status': 'success', 'size': actual_size, 'decrypted': True})
                else:
                    print(f"  ✗ 解密失败")
                    results.append({'idx': idx, 'title': title, 'status': 'decrypt_failed', 'size': actual_size})
            else:
                if verify_mp4(output):
                    print(f"  ✓ 无需解密，验证通过")
                    results.append({'idx': idx, 'title': title, 'status': 'success', 'size': actual_size, 'decrypted': False})
                else:
                    print(f"  ✗ 验证失败")
                    results.append({'idx': idx, 'title': title, 'status': 'verify_failed', 'size': actual_size})
        else:
            print(f"  ✗ 下载失败")
            results.append({'idx': idx, 'title': title, 'status': 'download_failed'})
    
    # 保存结果
    result_file = os.path.join(output_dir, 'download_results.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 统计
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if 'failed' in r['status'])
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    print(f"\n=== 下载完成 ===")
    print(f"成功: {success}, 失败: {failed}, 跳过: {skipped}")
    print(f"结果已保存: {result_file}")

if __name__ == '__main__':
    main()
