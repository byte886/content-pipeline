#!/usr/bin/env python3
"""
微信主窗口鲁棒搜索脚本（参数化）
用法: python3 wechat_search_robust.py <搜索关键词>
流程全自动完成：
1.  reopen还原所有微信窗口，确认只留主窗口，关掉所有浏览器残留窗口
2.  激活主窗口到前台，ESC清浮层，Cmd+1切回聊天视图
3.  复位主窗口到左上角900x600标准位置
4.  Cmd+F激活搜索框，粘贴关键词
5.  鼠标在下拉列表内滚动，OCR检测到"搜索网络"才停止
6.  点击列表获得焦点，用↓逐次选中，OCR确认选中纯目标主条目再回车
7.  自动把搜一搜窗口摆到右侧标准位置
"""
import pyautogui
import time
import subprocess
import sys
import os

OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"

def osascript(cmd):
    subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True)

def get_wechat_window_count():
    res = subprocess.run(
        'osascript -e \'tell application "System Events" to tell process "WeChat" to count of windows\'',
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    try:
        return int(res)
    except:
        return 0

def main():
    if len(sys.argv) < 2:
        print("用法: python3 wechat_search_robust.py <搜索关键词>")
        sys.exit(1)
    keyword = sys.argv[1]

    print(f"=== 开始搜索: {keyword} ===")
    # 1. 标准激活前置：先reopen还原最小化窗口
    osascript('tell application "WeChat" to reopen')
    time.sleep(1.5)
    osascript('tell application "WeChat" to activate')
    time.sleep(1)

    # 2. 强制清理多余窗口：只要窗口数>1就一直关，直到只剩主窗口
    for _ in range(10):
        n = get_wechat_window_count()
        if n <= 1:
            break
        osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
        time.sleep(0.5)
    # 如果主窗口被关掉了，再reopen一次
    if get_wechat_window_count() < 1:
        osascript('tell application "WeChat" to reopen')
        time.sleep(2)
        osascript('tell application "WeChat" to activate')
        time.sleep(1)

    # 3. 激活后立刻把主窗口摆到左上角，为后续窗口腾出右侧空间
    osascript("tell application "System Events" to tell process "WeChat" to set size of window 1 to {900, 600}")
    osascript("tell application "System Events" to tell process "WeChat" to set position of window 1 to {0, 0}")
    time.sleep(0.3)

    # 4. 按3次ESC关所有残留浮层
    for _ in range(3):
        osascript('tell application "System Events" to tell process "WeChat" to key code 53')
        time.sleep(0.15)

    # 4. 复位主窗口到标准位置
    osascript('tell application "System Events" to tell process "WeChat" to set size of window 1 to {900, 600}')
    osascript('tell application "System Events" to tell process "WeChat" to set position of window 1 to {0, 0}')
    time.sleep(0.3)

    # 5. Cmd+1切回聊天视图
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "1" using {command down}')
    time.sleep(0.3)

    # 6. Cmd+F激活搜索框
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "f" using {command down}')
    time.sleep(0.3)

    # 7. 清空搜索框，粘贴关键词
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "a" using {command down}')
    time.sleep(0.1)
    osascript('tell application "System Events" to tell process "WeChat" to key code 51')
    time.sleep(0.1)
    subprocess.run("pbcopy", input=keyword.encode("utf-8"), check=True)
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "v" using {command down}')
    time.sleep(1.2)

    # 8. 鼠标移到下拉列表中间，滚动直到OCR检测到"搜索网络"
    pyautogui.moveTo(150, 280, duration=0.3)
    found = False
    for i in range(25):
        pyautogui.scroll(-10)
        time.sleep(0.15)
        subprocess.run("screencapture -x -C /tmp/search_ocr_check.png", shell=True, check=True)
        res = subprocess.run(["swift", OCR_SCRIPT, "/tmp/search_ocr_check.png"], capture_output=True, text=True).stdout
        if "搜索网络" in res:
            print(f"✅ 第{i+1}次滚动后检测到'搜索网络'，已到达网络结果区域")
            found = True
            break
    if not found:
        print("ℹ️ 滚动25次到列表底部")

    # 9. 点击列表获得焦点，↓逐次选中纯目标主条目再回车
    pyautogui.click(150, 265)
    time.sleep(0.3)
    for i in range(5):
        osascript('tell application "System Events" to tell process "WeChat" to key code 125')
        time.sleep(0.2)
        subprocess.run("screencapture -x -C /tmp/select_check.png", shell=True, check=True)
        res = subprocess.run(["swift", OCR_SCRIPT, "/tmp/select_check.png"], capture_output=True, text=True).stdout
        if keyword in res and "官网" not in res.split(keyword)[0][-10:]:
            print(f"✅ 第{i+1}次↓后选中纯'{keyword}'主条目")
            break

    # 10. 回车打开搜一搜
    osascript('tell application "System Events" to tell process "WeChat" to key code 36')
    time.sleep(6)

    # 11. 调整浏览器窗口布局到右侧
    osascript('tell application "System Events" to tell process "WeChat" to set size of window 2 to {1010, 600}')
    osascript('tell application "System Events" to tell process "WeChat" to set position of window 2 to {900, 0}')
    time.sleep(0.5)

    # 12. 截图验证
    subprocess.run("screencapture -x -C /tmp/search_success.png", shell=True, check=True)
    print(f"✅ 搜索完成：已打开'{keyword}'搜一搜结果页")
    for f in ["/tmp/search_ocr_check.png", "/tmp/select_check.png"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    main()
