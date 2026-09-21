#!/usr/bin/env python3
"""
微信视频号批量下载脚本 v4
- 使用换签后的可播放直链下载（URL 须含 token，来自 video-capture 捕获的 handleMedia 落库）
- 短视频(Isaac64 加密前128KB)调用同目录 Node 解密器；直播回放为明文 MP4 不解密
- ftyp 校验 + md5 对账 + 去重命名 + 结果 manifest

环境变量（可选）:
  WC_PROXY   下载代理，如 http://127.0.0.1:8899（默认直连；finder.video.qq.com 国内 CDN 通常直连即可）
  WC_LIMIT   只处理前 N 条（验证用）
  WC_NODE    node 可执行文件路径（默认 PATH 中的 node）
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DECRYPT_JS = os.path.join(HERE, 'wechat_decrypt.js')
PROXY = os.environ.get('WC_PROXY', '').strip()
NODE = os.environ.get('WC_NODE', 'node').strip() or 'node'


def download_video(url, output, max_retries=3, quality='default'):
    """下载视频
    quality: default(默认), max(最大xWT111), min(最小xWT128)
    """
    # 根据质量参数修改URL（URL 未显式带清晰度标识时才追加）
    if quality == 'max' and 'X-snsvideoflag' not in url:
        url += '&X-snsvideoflag=xWT111'
    elif quality == 'min' and 'X-snsvideoflag' not in url:
        url += '&X-snsvideoflag=xWT128'

    for attempt in range(max_retries):
        if os.path.exists(output):
            os.remove(output)
        cmd = [
            'curl', '-L', '-sS', '-f', '-o', output,
            '-H', 'Referer: https://channels.weixin.qq.com/',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
            '--connect-timeout', '30',
            '--max-time', '600',
        ]
        if PROXY:
            cmd += ['-x', PROXY, '-k']
        cmd.append(url)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0 and os.path.exists(output) \
                and os.path.getsize(output) > 1000:
            return True
        if result is not None and result.stderr:
            print(f"  curl: {result.stderr.strip()[:200]}")
        time.sleep(2)
    return False


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def decrypt_video(filepath, decode_key):
    """解密视频（仅前128KB，原地）"""
    if not decode_key:
        return True
    cmd = [NODE, DECRYPT_JS, str(decode_key), filepath]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

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

    limit = os.environ.get('WC_LIMIT', '').strip()
    if limit:
        videos = videos[:int(limit)]

    print(f"开始下载 {len(videos)} 个视频到 {output_dir}")
    print(f"类型: {video_type}, 起始序号: {start_idx}, 代理: {PROXY or '直连'}")
    
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
        
        expected_md5 = (v.get('md5') or '').lower()
        if success:
            actual_size = os.path.getsize(output)
            print(f"  下载完成: {actual_size/1024/1024:.1f}MB")

            # 解密（仅短视频需要）后做 ftyp 校验
            if decode_key:
                print(f"  解密中...")
                ok = decrypt_video(output, decode_key) and verify_mp4(output)
            else:
                ok = verify_mp4(output)

            if ok:
                actual_md5 = md5_of(output)
                md5_match = (actual_md5 == expected_md5) if expected_md5 else None
                tag = '解密成功' if decode_key else '明文MP4'
                print(f"  ✓ {tag} ftyp校验通过  md5={actual_md5[:12]}"
                      f"{'  ✓md5一致' if md5_match is True else ('  (md5规格不同)' if md5_match is False else '')}")
                results.append({
                    'idx': idx, 'title': title, 'status': 'success',
                    'file': os.path.basename(output), 'size': actual_size,
                    'expected_size': expected_size, 'decrypted': bool(decode_key),
                    'md5': actual_md5, 'expected_md5': expected_md5 or None,
                    'md5_match': md5_match,
                })
            else:
                print(f"  ✗ 解密/校验失败")
                results.append({'idx': idx, 'title': title,
                                'status': 'decrypt_failed' if decode_key else 'verify_failed',
                                'size': actual_size})
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
