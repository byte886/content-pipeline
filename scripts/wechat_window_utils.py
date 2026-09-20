#!/usr/bin/env python3
"""微信窗口判别与管理工具"""
import subprocess, time

def osascript(cmd):
    return subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True, text=True).stdout.strip()

def list_wechat_windows():
    """返回所有微信窗口的标题列表"""
    res = osascript('''
tell application "System Events"
    tell process "WeChat"
        set titles to {}
        repeat with w in windows
            copy (name of w) to end of titles
        end repeat
        return titles as string
    end tell
end tell
''')
    return [t.strip() for t in res.split(",") if t.strip()]

def clean_wechat_windows():
    """只保留标题为'微信'的主窗口，关闭所有其他子窗口（浏览器/文章/视频号）"""
    for _ in range(15):
        titles = list_wechat_windows()
        main_count = sum(1 for t in titles if t == "微信")
        other_count = len(titles) - main_count
        if other_count == 0 and main_count >= 1:
            break
        # 关闭最前面的非主窗口
        osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
        time.sleep(0.6)
    print(f"✅ 窗口清理完成，剩余窗口: {list_wechat_windows()}")

def get_main_window_rect():
    """找到标题为'微信'的主窗口，返回它的position/size"""
    res = osascript('''
tell application "System Events"
    tell process "WeChat"
        repeat with w in windows
            if name of w is "微信" then
                set p to position of w
                set s to size of w
                return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s) & "," & (item 2 of s)
            end if
        end repeat
    end tell
end tell
''')
    import re
    nums = [int(x) for x in re.findall(r'\d+', res)]
    if len(nums)>=4:
        return nums[0], nums[1], nums[2], nums[3]
    return 0,0,900,600
