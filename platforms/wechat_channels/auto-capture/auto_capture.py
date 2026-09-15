#!/usr/bin/env python3
"""
微信视频号自动化采集脚本

功能：自动搜索视频号 → 进入主页 → 滚动列表 → 捕获视频URL → 下载

用法：
    python3 auto_capture.py <视频号名称> [选项]

选项：
    --port 8899          代理端口
    --output videos.json 输出文件
    --download-dir ./downloads  下载目录
    --no-download        只捕获不下载
    --scroll-timeout 60  滚动超时时间（秒）
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class WeChatController:
    """微信界面控制器"""

    def __init__(self):
        self.app_name = "WeChat"

    def _osascript(self, script):
        """执行AppleScript"""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.stderr.strip()

    def activate(self):
        """激活微信窗口"""
        self._osascript(f'tell application "{self.app_name}" to activate')
        time.sleep(0.5)
        # 恢复最小化窗口
        self._osascript('''
            tell application "System Events"
                tell process "WeChat"
                    repeat 2 times
                        if (count of windows) > 0 then
                            try
                                set miniaturized of window 1 to false
                                exit repeat
                            end try
                        end if
                        delay 0.2
                    end repeat
                end tell
            end tell
        ''')
        time.sleep(0.3)

    def get_window_rect(self):
        """获取微信窗口位置和大小"""
        script = '''
            tell application "System Events"
                tell process "WeChat"
                    set targetWindow to missing value
                    repeat with w in windows
                        try
                            if name of w is "微信" then
                                set targetWindow to w
                                exit repeat
                            end if
                        end try
                    end repeat
                    if targetWindow is missing value then
                        set targetWindow to window 1
                    end if
                    set {x, y} to position of targetWindow
                    set {w0, h0} to size of targetWindow
                    return (x as integer) & "," & (y as integer) & "," & (w0 as integer) & "," & (h0 as integer)
                end tell
            end tell
        '''
        stdout, _ = self._osascript(script)
        parts = stdout.split(",")
        if len(parts) == 4:
            return tuple(int(p) for p in parts)
        return None

    def click_at(self, x, y):
        """点击指定坐标"""
        script = f'''
            ObjC.import('CoreGraphics')
            ObjC.import('Foundation')
            function mouseEvent(type, x, y) {{
                return $.CGEventCreateMouseEvent(null, type, {{x:x, y:y}}, $.kCGMouseButtonLeft)
            }}
            function post(event) {{
                $.CGEventPost($.kCGHIDEventTap, event)
            }}
            const clickX = {x}
            const clickY = {y}
            post(mouseEvent($.kCGEventMouseMoved, clickX, clickY))
            $.NSThread.sleepForTimeInterval(0.05)
            post(mouseEvent($.kCGEventLeftMouseDown, clickX, clickY))
            post(mouseEvent($.kCGEventLeftMouseUp, clickX, clickY))
        '''
        subprocess.run(["osascript", "-l", "JavaScript", "-e", script],
                       capture_output=True, timeout=5)
        time.sleep(0.3)

    def press_key(self, key_code, modifiers=None):
        """按键"""
        mod_str = ""
        if modifiers:
            mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"
        script = f'''
            tell application "System Events"
                tell process "WeChat"
                    key code {key_code}{mod_str}
                end tell
            end tell
        '''
        self._osascript(script)
        time.sleep(0.2)

    def type_text(self, text):
        """输入文本"""
        # 用剪贴板粘贴，避免中文输入问题
        subprocess.run(["pbcopy"], input=text.encode(), timeout=5)
        self._osascript('''
            tell application "System Events"
                tell process "WeChat"
                    keystroke "v" using {command down}
                end tell
            end tell
        ''')
        time.sleep(0.3)

    def search(self, keyword):
        """Cmd+F搜索"""
        self.activate()
        # Cmd+F
        self.press_key(3, ["command"])  # Cmd+F
        time.sleep(0.3)
        # 全选清空
        self.press_key(0, ["command"])  # Cmd+A
        time.sleep(0.1)
        self.press_key(51)  # Delete
        time.sleep(0.1)
        # 输入关键词
        self.type_text(keyword)
        time.sleep(0.5)
        # 回车选中第一个结果
        self.press_key(36)  # Return
        time.sleep(1.0)

    def scroll_down(self, clicks=5):
        """向下滚动（用鼠标滚轮事件）"""
        rect = self.get_window_rect()
        if not rect:
            return
        x, y, w, h = rect
        # 在窗口中间偏下的位置滚动
        scroll_x = x + w // 2
        scroll_y = y + h // 2

        script = f'''
            ObjC.import('CoreGraphics')
            ObjC.import('Foundation')
            function post(event) {{
                $.CGEventPost($.kCGHIDEventTap, event)
            }}
            // 移动鼠标到滚动区域
            const moveEvent = $.CGEventCreateMouseEvent(null, $.kCGEventMouseMoved, {{x:{scroll_x}, y:{scroll_y}}}, $.kCGMouseButtonLeft)
            post(moveEvent)
            $.NSThread.sleepForTimeInterval(0.1)
            // 滚动
            for (let i = 0; i < {clicks}; i++) {{
                const scrollEvent = $.CGEventCreateScrollWheelEvent(null, $.kCGScrollEventUnitLine, 2, 30, 0)
                post(scrollEvent)
                $.NSThread.sleepForTimeInterval(0.05)
            }}
        '''
        subprocess.run(["osascript", "-l", "JavaScript", "-e", script],
                       capture_output=True, timeout=10)
        time.sleep(0.5)


class VideoCapture:
    """视频捕获工具管理"""

    def __init__(self, port, output_file, capture_tool_dir):
        self.port = port
        self.output_file = output_file
        self.capture_tool_dir = capture_tool_dir
        self.process = None

    def start(self):
        """启动捕获工具"""
        tool_path = os.path.join(self.capture_tool_dir, "video-capture")
        cmd = [tool_path, "-port", str(self.port), "-output", self.output_file]
        print(f"[捕获] 启动: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            cwd=self.capture_tool_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        # 等待代理设置完成
        time.sleep(3)
        print("[捕获] 代理已设置，等待微信流量...")

    def stop(self):
        """停止捕获工具（发送SIGINT，触发代理清除）"""
        if self.process and self.process.poll() is None:
            print("[捕获] 正在停止，清除系统代理...")
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("[捕获] 已停止，代理已清除")

    def get_videos(self):
        """读取捕获的视频列表"""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                return json.load(f)
        return []


def auto_capture(channel_name, port, output_file, download_dir, no_download, scroll_timeout):
    """自动化采集主流程"""
    project_root = Path(__file__).parent.parent.parent
    capture_tool_dir = project_root / "tools" / "video-capture"
    downloader_dir = project_root / "tools" / "video-downloader"

    wechat = WeChatController()
    capture = VideoCapture(port, output_file, str(capture_tool_dir))

    try:
        # 1. 启动捕获工具
        capture.start()

        # 2. 激活微信并搜索
        print(f"\n[微信] 搜索视频号: {channel_name}")
        wechat.search(channel_name)

        # 3. 等待页面加载
        print("[微信] 等待页面加载...")
        time.sleep(3)

        # 4. 滚动"视频"标签
        print("\n[微信] 滚动视频列表...")
        last_count = 0
        no_change_count = 0
        start_time = time.time()

        while time.time() - start_time < scroll_timeout:
            wechat.scroll_down(clicks=8)
            time.sleep(1.5)

            # 检查捕获数量
            videos = capture.get_videos()
            current_count = len(videos)
            print(f"  已捕获: {current_count} 个资源")

            if current_count == last_count:
                no_change_count += 1
                if no_change_count >= 5:
                    print("  连续5次无新内容，认为已到底部")
                    break
            else:
                no_change_count = 0
            last_count = current_count

        # 5. 切换到"直播回放"标签（需要点击）
        print("\n[微信] 切换到直播回放标签...")
        rect = wechat.get_window_rect()
        if rect:
            x, y, w, h = rect
            # 点击标签栏位置（视频号页面顶部，需要根据实际情况调整）
            # 这里假设直播回放标签在视频标签右边
            tab_x = x + int(w * 0.6)
            tab_y = y + int(h * 0.15)
            wechat.click_at(tab_x, tab_y)
            time.sleep(2)

            # 滚动直播回放列表
            print("[微信] 滚动直播回放列表...")
            last_count = len(capture.get_videos())
            no_change_count = 0
            start_time = time.time()

            while time.time() - start_time < scroll_timeout:
                wechat.scroll_down(clicks=8)
                time.sleep(1.5)

                videos = capture.get_videos()
                current_count = len(videos)
                print(f"  已捕获: {current_count} 个资源")

                if current_count == last_count:
                    no_change_count += 1
                    if no_change_count >= 4:
                        print("  直播回放到底部")
                        break
                else:
                    no_change_count = 0
                last_count = current_count

        # 6. 等待最后一批URL捕获
        print("\n[捕获] 等待最后一批URL...")
        time.sleep(3)

        # 7. 停止捕获
        capture.stop()

        # 8. 统计结果
        videos = capture.get_videos()
        print(f"\n{'='*50}")
        print(f"采集完成！共捕获 {len(videos)} 个资源")
        print(f"输出文件: {output_file}")

        # 分类统计
        short_videos = [v for v in videos if v.get('size', 0) < 100 * 1024 * 1024]
        live_replays = [v for v in videos if v.get('size', 0) >= 100 * 1024 * 1024]
        print(f"  短视频: {len(short_videos)} 个")
        print(f"  直播回放: {len(live_replays)} 个")
        print(f"{'='*50}")

        # 9. 下载
        if not no_download and videos:
            print("\n[下载] 开始下载...")
            # 保存分类后的列表
            short_file = output_file.replace('.json', '_short.json')
            live_file = output_file.replace('.json', '_live.json')
            with open(short_file, 'w') as f:
                json.dump(short_videos, f, ensure_ascii=False, indent=2)
            with open(live_file, 'w') as f:
                json.dump(live_replays, f, ensure_ascii=False, indent=2)

            short_dir = os.path.join(download_dir, "短视频")
            live_dir = os.path.join(download_dir, "直播回放")
            os.makedirs(short_dir, exist_ok=True)
            os.makedirs(live_dir, exist_ok=True)

            # 下载短视频
            if short_videos:
                print(f"[下载] 短视频: {len(short_videos)} 个")
                subprocess.run([
                    sys.executable,
                    str(downloader_dir / "batch_download_v4.py"),
                    short_file, short_dir, "short", "1"
                ])

            # 下载直播回放
            if live_replays:
                print(f"[下载] 直播回放: {len(live_replays)} 个")
                subprocess.run([
                    sys.executable,
                    str(downloader_dir / "batch_download_v4.py"),
                    live_file, live_dir, "live", "1"
                ])

            print("\n[下载] 全部完成！")

    except KeyboardInterrupt:
        print("\n\n用户中断，正在清理...")
        capture.stop()
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        capture.stop()
        raise


def main():
    parser = argparse.ArgumentParser(description="微信视频号自动化采集")
    parser.add_argument("channel_name", help="视频号名称")
    parser.add_argument("--port", type=int, default=8899, help="代理端口")
    parser.add_argument("--output", default="videos.json", help="输出文件")
    parser.add_argument("--download-dir", default="./downloads", help="下载目录")
    parser.add_argument("--no-download", action="store_true", help="只捕获不下载")
    parser.add_argument("--scroll-timeout", type=int, default=60, help="滚动超时(秒)")
    args = parser.parse_args()

    print("=" * 50)
    print("  微信视频号自动化采集工具")
    print("=" * 50)
    print(f"视频号: {args.channel_name}")
    print(f"代理端口: {args.port}")
    print(f"输出文件: {args.output}")
    print(f"下载目录: {args.download_dir}")
    print(f"只捕获不下载: {args.no_download}")
    print("=" * 50)

    auto_capture(
        args.channel_name,
        args.port,
        args.output,
        args.download_dir,
        args.no_download,
        args.scroll_timeout
    )


if __name__ == "__main__":
    main()
