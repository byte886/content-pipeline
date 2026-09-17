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
    """B站增量采集 — 内联wbi签名获取UP主动态（不走subprocess，避免环境差异）"""

    UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    MIXIN_TAB = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,
                 14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,
                 56,59,6,63,57,62,11,36,20,34,44,52]

    def _wbi_sign(self, params: dict, img_key: str, sub_key: str) -> str:
        """wbi签名"""
        import hashlib, urllib.parse, time
        mixin_key = img_key + sub_key
        mixin = ''.join([mixin_key[i] for i in self.MIXIN_TAB])[:32]
        params['wts'] = int(time.time())
        params = dict(sorted(params.items()))
        query = urllib.parse.urlencode(params)
        wbi_sign = hashlib.md5((query + mixin).encode()).hexdigest()
        params['w_rid'] = wbi_sign
        return urllib.parse.urlencode(params)

    def _get_chrome_sessdata(self) -> str:
        """从Chrome读取B站SESSDATA cookie（已登录态），失败返回空字符串"""
        import subprocess, tempfile, os
        ruby_script = '''
require "sqlite3"
require "openssl"
password = `security find-generic-password -w -a Chrome -s "Chrome Safe Storage"`.strip
key = OpenSSL::PKCS5.pbkdf2_hmac(password, "saltysalt", 1003, 16, OpenSSL::Digest::SHA1.new)
cookies_db = File.expand_path("~/Library/Application Support/Google/Chrome/Default/Cookies")
db = SQLite3::Database.new(cookies_db)
rows = db.execute("SELECT encrypted_value FROM cookies WHERE host_key LIKE '%bilibili.com' AND name='SESSDATA'")
db.close
rows.each do |enc_val|
  enc_val = enc_val[0]
  next unless enc_val && enc_val.bytes[0..2] == [118, 49, 48]
  iv = enc_val.bytes[3..18].pack("C*")
  ciphertext = enc_val.bytes[19..].pack("C*")
  decipher = OpenSSL::Cipher.new("AES-128-CBC")
  decipher.decrypt
  decipher.key = key
  decipher.iv = iv
  decrypted = decipher.update(ciphertext) + decipher.final
  pad_len = decrypted.bytes[-1]
  val = decrypted.bytes[0...-pad_len].pack("C*")
  idx = val.index(/[0-9a-f]{8}/)
  val = val[idx..] if idx
  if val && val.length > 50 && val.include?("%2C")
    print val
    exit 0
  end
end
'''
        try:
            result = subprocess.run(['ruby', '-e', ruby_script], capture_output=True, timeout=15)
            val = result.stdout.decode('utf-8', errors='ignore').strip()
            if val and len(val) > 50:
                return val
        except Exception:
            pass
        return ''

    def _get_wbi_keys(self) -> tuple:
        """获取wbi img_key和sub_key（带登录cookie）"""
        import urllib.request, http.cookiejar
        sessdata = self._get_chrome_sessdata()
        cj = http.cookiejar.CookieJar()
        if sessdata:
            # 手动注入SESSDATA
            import http.cookiejar as cj_mod
            cookie = cj_mod.Cookie(
                version=0, name='SESSDATA', value=sessdata,
                port=None, port_specified=False,
                domain='.bilibili.com', domain_specified=True, domain_initial_dot=True,
                path='/', path_specified=True,
                secure=True, expires=None, discard=True,
                comment=None, comment_url=None, rest={}, rfc2109=False
            )
            cj.set_cookie(cookie)
        # 强制直连，不走代理
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPCookieProcessor(cj)
        )
        # 获取nav接口的wbi keys
        req = urllib.request.Request(
            "https://api.bilibili.com/x/web-interface/nav",
            headers={'User-Agent': self.UA, 'Referer': 'https://www.bilibili.com/'}
        )
        with opener.open(req, timeout=10) as r:
            data = json.loads(r.read())
        wbi = data['data']['wbi_img']
        img_key = wbi['img_url'].rsplit('/', 1)[1].split('.')[0]
        sub_key = wbi['sub_url'].rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key, opener

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """内联wbi签名获取UP主最新视频列表"""
        import urllib.request
        uid = self.config.get('uid', '')
        if not uid:
            raise ValueError("B站UID未配置")

        img_key, sub_key, opener = self._get_wbi_keys()

        params = {
            'mid': uid,
            'ps': 50,
            'pn': 1,
            'order': 'pubdate',
        }
        signed_query = self._wbi_sign(params, img_key, sub_key)
        url = f"https://api.bilibili.com/x/space/wbi/arc/search?{signed_query}"

        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': self.UA,
                'Referer': f'https://space.bilibili.com/{uid}/video',
                'Origin': 'https://space.bilibili.com',
            }
        )
        with opener.open(req, timeout=15) as r:
            data = json.loads(r.read())

        if data.get('code') != 0:
            raise Exception(f"B站API错误: {data.get('message')} (code={data.get('code')})")

        videos = data['data']['list']['vlist']
        result = []
        for v in videos:
            result.append({
                'bvid': v['bvid'],
                'title': v['title'],
                'url': f"https://www.bilibili.com/video/{v['bvid']}",
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
    """公众号增量采集 — 从网络捕获的JSON读取文章列表

    公众号没有公开API，需要通过res-downloader等工具捕获文章列表页请求。
    下载：复用已有的公众号文章采集脚本（platforms/wechat_official/）
    """

    def __init__(self, account: str, domain: str, platform: str, config: dict = None):
        super().__init__(account, domain, platform, config)
        self.list_file = self.config.get('list_file', '')

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """从网络捕获的JSON文件读取最新文章列表"""
        if not self.list_file or not Path(self.list_file).exists():
            raise Exception(
                f"公众号列表文件不存在: {self.list_file}\n"
                f"请先用res-downloader捕获公众号文章列表页，保存为JSON后指定 --list-file"
            )
        with open(self.list_file, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'list' in data:
            return data['list']
        if isinstance(data, dict) and 'articles' in data:
            return data['articles']
        return []

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        # 公众号文章URL含__biz和mid，是唯一的
        url = item.get('url', item.get('link', ''))
        if url:
            return url
        return item.get('title', '')

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """下载公众号文章（调用已有的采集脚本）"""
        import subprocess
        url = item.get('url', item.get('link', ''))
        if not url:
            return None

        title = item.get('title', f'article_{index}').replace('/', '_')[:50]
        output_dir = LIBRARY_DIR / "06_articles" / self.domain / self.account
        output_dir.mkdir(parents=True, exist_ok=True)

        # 调用已有的公众号文章采集脚本
        article_script = PROJECT_DIR / "platforms" / "wechat_official" / "fetch_article.py"
        if article_script.exists():
            try:
                cmd = [
                    sys.executable, str(article_script),
                    url, '--output', str(output_dir)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=60, cwd=str(PROJECT_DIR))
                # 查找新创建的文章目录
                article_dirs = sorted(output_dir.glob("*/"), key=lambda d: d.stat().st_mtime, reverse=True)
                if article_dirs and (article_dirs[0].stat().st_mtime > __import__('time').time() - 60):
                    return article_dirs[0]
            except Exception as e:
                print(f"下载失败: {e}")
        else:
            print(f"公众号采集脚本不存在: {article_script}")
        return None


class DouyinFetcher(IncrementalFetcher):
    """抖音增量采集 — 复用multiplatform-media-fetch的media_downloader.py

    列表获取：需要从抖音网页版或分享链接获取（反爬严格，目前支持单条下载）
    下载：media_downloader.py（匿名设备票据ttwid，公开视频免登录）
    """

    SKILL_DIR = Path.home() / "Doubao" / "skills" / "multiplatform-media-fetch"
    DOWNLOADER = SKILL_DIR / "scripts" / "media_downloader.py"

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """抖音列表获取需手动提供（反爬严格）

        支持两种方式：
        1. --list-file 指定JSON列表
        2. 配置中指定 sec_uid，调用抖音网页版（可能被反爬）
        """
        list_file = self.config.get('list_file', '')
        if list_file and Path(list_file).exists():
            with open(list_file, encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else data.get('list', [])

        # 尝试从配置的分享链接获取单条
        share_url = self.config.get('share_url', '')
        if share_url:
            return [{'url': share_url, 'title': '抖音视频', 'type': 'video'}]

        raise Exception(
            "抖音列表获取需指定 --list-file 或在config中配置share_url\n"
            "（抖音反爬严格，自动获取用户全部作品列表暂不可用）"
        )

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        # 抖音纯数字ID或URL
        aweme_id = item.get('aweme_id', item.get('id', ''))
        if aweme_id:
            return str(aweme_id)
        url = item.get('url', '')
        # 从URL提取数字ID
        import re
        match = re.search(r'/(\d{15,})', url)
        if match:
            return match.group(1)
        return url

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """调用media_downloader.py下载抖音视频"""
        import subprocess
        url = item.get('url', '')
        if not url:
            return None

        title = item.get('title', f'douyin_{index}').replace('/', '_')[:50]
        output_dir = LIBRARY_DIR / "01_video" / self.domain / self.account
        output_dir.mkdir(parents=True, exist_ok=True)

        # 抖音强制直连，清除代理
        env = os.environ.copy()
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            env.pop(key, None)

        try:
            cmd = [
                sys.executable, str(self.DOWNLOADER),
                url, '--quality', '720',
                '-o', str(output_dir)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=120, env=env, cwd=str(PROJECT_DIR))
            # 查找下载的文件
            files = list(output_dir.glob(f"*{title}*"))
            if files:
                return files[0]
            # 按时间找最新文件
            files = sorted(output_dir.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
            if files and (files[0].stat().st_mtime > __import__('time').time() - 120):
                return files[0]
        except Exception as e:
            print(f"下载失败: {e}")
        return None


class YoutubeFetcher(IncrementalFetcher):
    """YouTube增量采集 — 复用media_downloader.py + yt-dlp

    列表获取：yt-dlp获取频道/播放列表视频
    下载：media_downloader.py（需要代理）
    """

    SKILL_DIR = Path.home() / "Doubao" / "skills" / "multiplatform-media-fetch"
    DOWNLOADER = SKILL_DIR / "scripts" / "media_downloader.py"

    def fetch_latest_list(self) -> List[Dict[str, Any]]:
        """用yt-dlp获取频道最新视频列表"""
        import subprocess
        channel_url = self.config.get('channel_url', '')
        if not channel_url:
            raise Exception("YouTube频道URL未配置（config.channel_url）")

        # 用yt-dlp获取频道最新视频（flat-playlist只获取元数据不下载）
        env = os.environ.copy()
        # YouTube需要代理，确保代理环境变量存在
        proxy = env.get('HTTPS_PROXY', env.get('https_proxy', 'http://127.0.0.1:7890'))
        env['HTTPS_PROXY'] = proxy
        env['HTTP_PROXY'] = proxy

        try:
            cmd = [
                'yt-dlp', '--flat-playlist', '--dump-json',
                '--playlist-end', '30',  # 最新30条
                channel_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=60, env=env, cwd=str(PROJECT_DIR))
            items = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        v = json.loads(line)
                        items.append({
                            'video_id': v.get('id', ''),
                            'title': v.get('title', ''),
                            'url': f"https://www.youtube.com/watch?v={v.get('id', '')}",
                            'duration': v.get('duration', 0),
                            'type': 'video',
                        })
                    except json.JSONDecodeError:
                        continue
            return items
        except Exception as e:
            raise Exception(f"yt-dlp获取频道列表失败: {e}")

    def get_unique_key(self, item: Dict[str, Any]) -> str:
        return item.get('video_id', item.get('url', ''))

    def download_item(self, item: Dict[str, Any], index: int) -> Optional[Path]:
        """调用media_downloader.py下载YouTube视频"""
        import subprocess
        url = item.get('url', '')
        if not url:
            return None

        output_dir = LIBRARY_DIR / "01_video" / self.domain / self.account
        output_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        proxy = env.get('HTTPS_PROXY', env.get('https_proxy', 'http://127.0.0.1:7890'))
        env['HTTPS_PROXY'] = proxy
        env['HTTP_PROXY'] = proxy

        try:
            cmd = [
                sys.executable, str(self.DOWNLOADER),
                url, '--quality', '720',
                '-o', str(output_dir)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=300, env=env, cwd=str(PROJECT_DIR))
            files = sorted(output_dir.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
            if files and (files[0].stat().st_mtime > __import__('time').time() - 300):
                return files[0]
        except Exception as e:
            print(f"下载失败: {e}")
        return None


# ============================================================
# 工厂和入口
# ============================================================

FETCHER_REGISTRY = {
    'bilibili': BilibiliFetcher,
    'wechat_channels': WechatChannelsFetcher,
    'wechat_official': WechatOfficialFetcher,
    'douyin': DouyinFetcher,
    'youtube': YoutubeFetcher,
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
