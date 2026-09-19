#!/usr/bin/env python3
"""
微信主窗口搜索脚本：
输入关键词后，自动在下拉列表滚动到底找到"搜索网络结果"区块，
点击该区块第一个条目，打开完整微信搜一搜结果页。
用法: python3 wechat_search.py "生财有术"
"""
import pyautogui
import time
import subprocess
import sys

def main():
    if len(sys.argv) < 2:
        print("用法: python3 wechat_search.py <搜索关键词>")
        sys.exit(1)
    keyword = sys.argv[1]
    
    # 1. 激活微信主窗口
    print("1. 激活微信主窗口")
    subprocess.run(["osascript", "-e", 'tell application "WeChat" to activate'])
    time.sleep(0.5)
    
    # 2. 点顶部搜索框
    print("2. 点击顶部搜索框")
    pyautogui.click(120, 45)
    time.sleep(0.3)
    
    # 3. 清空搜索框并粘贴关键词
    print(f"3. 输入关键词: {keyword}")
    pyautogui.hotkey("command", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    # 复制关键词到剪贴板
    subprocess.run(f'echo -n "{keyword}" | pbcopy', shell=True)
    pyautogui.hotkey("command", "v")
    time.sleep(1)
    
    # 4. 鼠标移到下拉列表中间位置，滚动到底部找到"搜索网络结果"
    print("4. 在下拉列表内滚动到底部")
    pyautogui.moveTo(120, 350)
    time.sleep(0.2)
    # 滚动15次足够到底
    for i in range(15):
        pyautogui.scroll(-10)
        time.sleep(0.1)
    
    # 5. 点击搜索网络结果下第一个条目
    print("5. 点击搜索网络结果第一个条目")
    pyautogui.click(120, 300)
    time.sleep(5)
    
    # 6. 截图验证
    pyautogui.screenshot("/tmp/wechat_search_auto.png")
    print("✅ 完整搜一搜结果页已打开，截图保存在/tmp/wechat_search_auto.png")

if __name__ == "__main__":
    main()
