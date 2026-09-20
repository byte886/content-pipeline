#!/usr/bin/env python3
"""微信窗口判别与管理工具"""
import subprocess, time, re

def osascript(cmd):
    return subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True, text=True).stdout.strip()

def list_wechat_windows():
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

# 已知的非主窗口标题关键词（出现这些就不是主窗口）
NON_MAIN_KEYWORDS = [
    "搜索聊天记录",
    "搜一搜",
    "公众号",
    "视频号",
    "文章",
]

def is_main_window(title):
    t = title.strip()
    # 命中非主窗口关键词的直接排除
    for kw in NON_MAIN_KEYWORDS:
        if kw in t:
            return False
    # 主窗口标题很短，最长不超过"微信 (窗口)"的长度
    if len(t) > 10:
        return False
    return t.startswith("微信")

def clean_wechat_windows():
    for _ in range(15):
        titles = list_wechat_windows()
        mains = [t for t in titles if is_main_window(t)]
        others = [t for t in titles if not is_main_window(t)]
        if len(mains)>=1 and len(others)==0:
            break
        osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
        time.sleep(0.6)
    print(f"✅ 窗口清理完成，剩余窗口: {list_wechat_windows()}")

def get_main_window_rect():
    res = osascript('''
tell application "System Events"
    tell process "WeChat"
        repeat with w in windows
            set t to name of w
            if t starts with "微信" and length of t < 10 then
                set p to position of w
                set s to size of w
                return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s) & "," & (item 2 of s)
            end if
        end repeat
    end tell
end tell
''')
    nums = [int(x) for x in re.findall(r'\d+', res)]
    if len(nums)>=4:
        return nums[0], nums[1], nums[2], nums[3]
    return 0,0,900,600
