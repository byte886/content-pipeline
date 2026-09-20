#!/usr/bin/env python3
"""
微信主窗口鲁棒搜索脚本（全动态坐标版）
逻辑：
1.  激活微信，清理多余窗口
2.  尝试把主窗口复位到左上角900x600（如果微信沙盒不允许移动也没关系）
3.  读取主窗口实际position/size
4.  基于实际窗口位置动态计算所有点击坐标
5.  执行搜索、滚动下拉列表、点击目标条目打开搜一搜
"""
import pyautogui, time, subprocess, sys, os, re

OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
TARGET_W, TARGET_H = 900, 600

def osascript(cmd):
    return subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True, text=True).stdout.strip()

def get_win_count():
    res = osascript('tell application "System Events" to tell process "WeChat" to count of windows')
    try: return int(res)
    except: return 0

def get_wechat_rect():
    """读取微信主窗口实际位置和大小，返回(x,y,w,h)"""
    res = osascript('''
tell application "System Events"
    tell process "WeChat"
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

    # 1. 激活微信
    osascript('tell application "WeChat" to reopen')
    time.sleep(1.5)
    osascript('tell application "WeChat" to activate')
    time.sleep(1)

    # 2. 清理多余窗口
    for _ in range(10):
        if get_win_count() <=1: break
        osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
        time.sleep(0.5)

    # 3. 尝试复位窗口到左上角（沙盒不生效也没关系，后面读实际坐标）
    osascript(f'tell application "System Events" to tell process "WeChat" to set size of window 1 to {{{TARGET_W}, {TARGET_H}}}')
    osascript('tell application "System Events" to tell process "WeChat" to set position of window 1 to {0, 0}')
    time.sleep(0.3)

    # 4. 强制ESC清浮层
    for _ in range(3):
        osascript('tell application "System Events" to tell process "WeChat" to key code 53')
        time.sleep(0.15)

    # 5. 读窗口实际位置（核心动态计算）
    wx, wy, ww, wh = get_wechat_rect()
    print(f"📏 微信主窗口实际坐标: ({wx},{wy}), 尺寸: {ww}x{wh}")

    # 6. 切聊天视图+开搜索框
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "1" using {command down}')
    time.sleep(0.3)
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "f" using {command down}')
    time.sleep(0.3)

    # 7. 清空搜索框，粘贴关键词
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "a" using {command down}')
    time.sleep(0.1)
    osascript('tell application "System Events" to tell process "WeChat" to key code 51')
    time.sleep(0.1)
    subprocess.run("pbcopy", input=keyword.encode(), check=True)
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "v" using {command down}')
    time.sleep(1.2)

    # 8. 基于窗口坐标计算下拉列表滚动区域：窗口内左侧1/3, 中间垂直位置
    scroll_x = wx + int(ww*0.25)
    scroll_y = wy + int(wh*0.5)
    pyautogui.moveTo(scroll_x, scroll_y, duration=0.3)

    found = False
    for i in range(25):
        pyautogui.scroll(-10)
        time.sleep(0.15)
        subprocess.run("screencapture -x -C /tmp/chk.png", shell=True, check=True)
        r = subprocess.run(["swift", OCR_SCRIPT, "/tmp/chk.png"], capture_output=True, text=True).stdout
        if "搜索网络" in r:
            print(f"✅ 第{i+1}次滚动到网络结果区")
            found = True
            break

    # 9. 计算"生财有术"条目坐标：搜索网络结果下方第一行
    target_x = wx + int(ww*0.25)
    target_y = wy + int(wh*0.35)
    pyautogui.moveTo(target_x, target_y, duration=0.3)
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(6)

    # 10. 截图验证
    subprocess.run("screencapture -x -C /tmp/search_success.png", shell=True, check=True)
    print("✅ 搜索流程执行完成")
    os.path.exists("/tmp/chk.png") and os.remove("/tmp/chk.png")

if __name__ == "__main__":
    main()
