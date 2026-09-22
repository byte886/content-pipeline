"""
微信视频号采集插件（WeChat Channels Fetcher）

实现 PlatformFetcher 接口，薄封装 captor MITM 捕获 + 解密下载流程。

人机边界：captor 注入的 Pinia action 驱动会【自动翻页枚举全量】，人工只需在
微信里搜索账号名 → 点「视频号」行进入主页（约 15 秒），无需滚动、无需播放。

端到端采集推荐直接用同目录 collect_channels.py 一键编排（启动→人工开窗→
all-done→增量下载→转写→台账），本类只保留接口级原语。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from platforms.base import PlatformFetcher, ContentItem


class WechatChannelsFetcher(PlatformFetcher):
    """微信视频号采集插件"""

    def __init__(self, capture_port: int = 8899, proxy_port: int = None):
        """
        Args:
            capture_port: captor MITM 监听端口（默认 8899）
            proxy_port: 上游代理端口（如 ClashX 的 7890）；None=国内直连（默认）。
                视频号是国内站点默认直连，仅在需要走代理时才传。
        """
        self.capture_port = capture_port
        self.proxy_port = proxy_port
        self._capture_process = None

        # 工具路径（相对于项目根目录）
        self._project_root = Path(__file__).parent.parent.parent
        self._capture_bin = self._project_root / "platforms/wechat_channels/video-capture/video-capture"
        self._decrypt_script = self._project_root / "platforms/wechat_channels/video-downloader/wechat_decrypt.js"
        self._download_script = self._project_root / "platforms/wechat_channels/video-downloader/batch_download_v4.py"

    @property
    def platform_id(self) -> str:
        return "wechat_channels"

    @property
    def platform_name(self) -> str:
        return "微信视频号"

    def start_capture(self, output_file: str) -> subprocess.Popen:
        """
        启动MITM捕获工具。

        Args:
            output_file: 捕获结果输出JSON文件路径

        Returns:
            捕获进程
        """
        cmd = [
            str(self._capture_bin),
            "-port", str(self.capture_port),
            "-replay-list", "-short-probe",   # 注入 Pinia action 自动翻页枚举
            "-output", output_file,
            # 国内视频号默认直连（显式空串），仅在给了上游端口时才走代理
            "-upstream", (f"http://127.0.0.1:{self.proxy_port}" if self.proxy_port else ""),
        ]

        self._capture_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self._capture_bin.parent)
        )
        time.sleep(2)  # 等待代理启动
        return self._capture_process

    def stop_capture(self):
        """停止捕获工具"""
        if self._capture_process:
            self._capture_process.terminate()
            try:
                self._capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._capture_process.kill()
            self._capture_process = None

    def fetch_urls(self, account: str, **kwargs) -> List[ContentItem]:
        """
        采集指定视频号的全部视频列表。

        注意：此方法需要一次人工开窗（微信 GUI 不允许 AI 自动化）！
        1. 启动捕获后，在微信搜索账号名 → 点「视频号」行进入主页
        2. 注入的 action 驱动会自动翻页枚举全量，无需手动滚动、无需播放
        3. 看到日志 all-done 后按回车继续

        Args:
            account: 视频号名称（如 "交易的游戏"）
            **kwargs:
                - output_file: 捕获结果文件路径（默认临时文件）
                - auto_mode: 自动模式（不等待人工，直接读取已有捕获文件）

        Returns:
            内容项列表
        """
        output_file = kwargs.get('output_file', f'/tmp/wechat_channels_{account}_capture.json')
        auto_mode = kwargs.get('auto_mode', False)

        if not auto_mode:
            # 启动捕获
            self.start_capture(output_file)
            print(f"捕获工具已启动（端口 {self.capture_port}）")
            print(f"请在微信搜索「{account}」并点【视频号】行进入主页（无需滚动/播放）")
            print("看到日志 all-done 后按回车继续...")
            input()
            self.stop_capture()
            time.sleep(1)  # 等待文件写入完成

        # 读取捕获结果
        items = self._parse_capture_file(output_file, account)
        return items

    def _parse_capture_file(self, capture_file: str, account: str) -> List[ContentItem]:
        """解析捕获结果文件为ContentItem列表"""
        if not os.path.exists(capture_file):
            return []

        with open(capture_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = []
        # 捕获格式可能是列表或包含videos字段的对象
        videos = data if isinstance(data, list) else data.get('videos', data.get('items', []))

        for i, v in enumerate(videos, 1):
            item = ContentItem(
                item_id=v.get('id', v.get('video_id', f'video_{i:03d}')),
                title=v.get('title', v.get('desc', f'视频_{i:03d}')),
                url=v.get('url', v.get('video_url', '')),
                content_type=v.get('type', 'video'),
                platform="wechat_channels",
                author=account,
                published_at=v.get('publish_time', v.get('create_time', None)),
                duration=v.get('duration', None),
                metadata={
                    'decode_key': v.get('decode_key', v.get('DecodeKey', '')),
                    'quality': v.get('quality', ''),
                    'size': v.get('size', 0),
                    'raw_url': v.get('raw_url', ''),
                }
            )
            items.append(item)

        return items

    def download(self, item: ContentItem, output_dir: str, **kwargs) -> str:
        """
        下载单个视频号视频（含解密）。

        Args:
            item: 内容项（必须包含url和decode_key）
            output_dir: 输出目录
            **kwargs:
                - quality: 清晰度参数（默认xWT111，高质量）

        Returns:
            下载后的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        url = item.url
        decode_key = item.metadata.get('decode_key', '')

        if not url:
            raise ValueError("内容项缺少URL")

        # 构建高质量URL
        quality = kwargs.get('quality', 'xWT111')
        if 'X-snsvideoflag' not in url and quality:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}X-snsvideoflag={quality}"

        # 下载文件
        filename = f"{item.item_id}_{item.title[:50]}.mp4"
        # 清理文件名中的非法字符
        filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
        output_path = os.path.join(output_dir, filename)

        # 使用curl下载
        cmd = ['curl', '-L', '-o', output_path, url]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"下载失败: {result.stderr}")

        # 如果有decode_key，需要解密
        if decode_key:
            self._decrypt_video(output_path, decode_key)

        return output_path

    def _decrypt_video(self, video_path: str, decode_key: str):
        """
        解密视频号视频。

        解密原理：DecodeKey → ISAAC64生成128KB数组 → XOR文件前128KB
        """
        # 复制解密依赖到/tmp（wechat_decrypt.js硬编码了/tmp/decrypt_node.js）
        decrypt_node = self._project_root / "platforms/wechat_channels/video-downloader/decrypt_node.js"
        if decrypt_node.exists():
            import shutil
            shutil.copy(decrypt_node, '/tmp/decrypt_node.js')

        # 调用Node.js解密脚本
        cmd = ['node', str(self._decrypt_script), video_path, decode_key]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"解密失败: {result.stderr}")

    def needs_authentication(self) -> bool:
        """视频号需要微信登录态"""
        return True

    def __del__(self):
        """析构时确保停止捕获"""
        self.stop_capture()


# 工厂函数
def create_fetcher(**kwargs) -> WechatChannelsFetcher:
    """创建微信视频号采集插件实例"""
    return WechatChannelsFetcher(**kwargs)
