#!/usr/bin/env python3
"""
微信主窗口鲁棒搜索脚本（全动态坐标+精确窗口判别版）
"""
import pyautogui, time, subprocess, sys, os, re

OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
TARGET_W, TARGET_H = 900, 600

def osascript(cmd):
    return subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True, text=True).stdout.strip()

def get_all_window_titles():
    """读取微信所有窗口的标题列表"""
    res = osascript('''
tell application "System Events"
    tell process "WeChat"
        set titles to {}
        repeat with w in windows
            set end of titles to name of w
        end repeat
        return titles as string
    end tell
end tell
''')
    return [t.strip() for t in res.split(",") if t.strip()]

def close_extra_windows():
    """只保留主窗口（标题=微信），关闭所有子窗口"""
    for _ in range(10):
        titles = get_all_window_titles()
        # 只剩主窗口就退出
        if len([t for t in titles if t == "微信"]) >= 1 and len(titles) == 1:
            break
        # 找非主窗口的窗口关掉
        osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
        time.sleep(0.4)

def get_wechat_main_rect():
    """读取标题为微信的主窗口的实际位置和大小"""
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
        -- 找不到就返回默认
        set p to position of window 1
        set s to size of window 1
        return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s) & "," & (item 2 of s)
    end tell
end tell
''')
    nums = [int(x) for x in re.findall(r'\d+', res)]
    if len(nums)>=4:
        return nums[0], nums[1], nums[2], nums[3]
    return 0,0,900,600

def main():
    keyword = sys.argv[1] if len(sys.argv)>1 else "生财有术"
    print(f"=== 开始搜索: {keyword} ===")

    osascript('tell application "WeChat" to reopen')
    time.sleep(1.5)
    osascript('tell application "WeChat" to activate')
    time.sleep(1)

    # 精确清理多余窗口，只留主窗口
    print("🧹 清理多余微信子窗口...")
    close_extra_windows()

    # 尝试复位主窗口
    osascript(f'tell application "System Events" to tell process "WeChat" to set size of window 1 to {{{TARGET_W}, {TARGET_H}}}')
    osascript('tell application "System Events" to tell process "WeChat" to set position of window 1 to {0, 0}')
    time.sleep(0.3)

    # ESC清浮层
    for _ in range(3):
        osascript('tell application "System Events" to tell process "WeChat" to key code 53')
        time.sleep(0.15)

    # 读主窗口实际坐标
    wx, wy, ww, wh = get_wechat_main_rect()
    print(f"📏 微信主窗口实际坐标: ({wx},{wy}), 尺寸: {ww}x{wh}")

    # 切聊天视图+搜索框
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "1" using {command down}')
    time.sleep(0.3)
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "f" using {command down}')
    time.sleep(0.3)

    # 输入关键词
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "a" using {command down}')
    time.sleep(0.1)
    osascript('tell application "System Events" to tell process "WeChat" to key code 51')
    time.sleep(0.1)
    subprocess.run("pbcopy", input=keyword.encode(), check=True)
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "v" using {command down}')
    time.sleep(1.2)

    # 动态计算下拉列表滚动位置
    scroll_x = wx + int(ww*0.25)
    scroll_y = wy + int(wh*0.5)
    pyautogui.moveTo(scroll_x, scroll_y, duration=0.3)

    for i in range(25):
        pyautogui.scroll(-10)
        time.sleep(0.15)
        subprocess.run("screencapture -x -C /tmp/chk.png", shell=True, check=True)
        r = subprocess.run(["swift", OCR_SCRIPT, "/tmp/chk.png"], capture_output=True, text=True).stdout
        if "搜索网络" in r:
            print(f"✅ 第{i+1}次滚动到网络结果区")
            break

    # 动态计算目标条目位置
    target_x = wx + int(ww*0.25)
    target_y = wy + int(wh*0.35)
    pyautogui.moveTo(target_x, target_y, duration=0.3)
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(6)

    subprocess.run("screencapture -x -C /tmp/search_success.png", shell=True, check=True)
    print("✅ 搜索流程执行完成")
    os.path.exists("/tmp/chk.png") and os.remove("/tmp/chk.png")

if __name__ == "__main__":
    main()
