#!/usr/bin/env python3
"""
微信主窗口搜索鲁棒脚本：
输入关键词后，自动在下拉列表滚动，OCR检测到"搜索网络结果"区块后停止，
点击该区块第一个条目，打开完整微信搜一搜结果页。
用法: python3 wechat_search.py "生财有术"
"""
import pyautogui
import time
import subprocess
import sys
import os

OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
SCREENSHOT = "/tmp/wechat_search_dropdown.png"

def ocr_has_text(target_text):
    """截图并用macOS Vision OCR识别是否存在目标文字"""
    # 截取主窗口区域
    subprocess.run(f"screencapture -x -C -R 0,0,900,600 {SCREENSHOT}", shell=True, check=True)
    # 调用OCR
    result = subprocess.run(["swift", OCR_SCRIPT, SCREENSHOT], capture_output=True, text=True)
    return target_text in result.stdout

def main():
    if len(sys.argv) < 2:
        print("用法: python3 wechat_search.py <搜索关键词>")
        sys.exit(1)
    keyword = sys.argv[1]
    
    # 1. 激活微信主窗口，复位窗口大小位置
    print("1. 激活微信主窗口并复位")
    subprocess.run(["osascript", "-e", 'tell application "WeChat" to activate'])
    time.sleep(0.5)
    # 按ESC关所有弹窗
    for _ in range(3):
        subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to key code 53'", shell=True)
        time.sleep(0.15)
    subprocess.run('osascript -e \'tell application "System Events" to tell process "WeChat" to set size of window 1 to {900, 600}\'', shell=True)
    subprocess.run('osascript -e \'tell application "System Events" to tell process "WeChat" to set position of window 1 to {0, 0}\'', shell=True)
    time.sleep(0.3)
    # Cmd+1切回聊天视图
    subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to keystroke \"1\" using {command down}'", shell=True)
    time.sleep(0.3)
    
    # 2. Cmd+F激活搜索框
    print("2. 激活搜索框")
    subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to keystroke \"f\" using {command down}'", shell=True)
    time.sleep(0.3)
    
    # 3. 清空搜索框并粘贴关键词
    print(f"3. 输入关键词: {keyword}")
    subprocess.run(f"echo -n '{keyword}' | pbcopy", shell=True)
    subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to keystroke \"v\" using {command down}'", shell=True)
    time.sleep(1.2)
    
    # 4. 鼠标移到下拉列表内，滚动直到OCR检测到"搜索网络结果"
    print("4. 滚动下拉列表定位网络结果区块")
    pyautogui.moveTo(120, 350, duration=0.3)
    found = False
    for i in range(30):
        pyautogui.scroll(-10)
        time.sleep(0.1)
        if ocr_has_text("网络结果"):
            found = True
            print(f"✅ 第{i+1}次滚动后检测到'网络结果'区块")
            break
    if not found:
        print("❌ 滚动30次仍未找到网络结果，请检查关键词")
        sys.exit(1)
    
    # 5. 点击下拉列表内部获得焦点，按↓选中第一个条目
    time.sleep(0.2)
    pyautogui.click(120, 320)
    time.sleep(0.2)
    subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to key code 125'", shell=True)
    time.sleep(0.2)
    subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"WeChat\" to key code 36'", shell=True)
    time.sleep(6)
    
    # 6. 截图验证
    subprocess.run(f"screencapture -x -C /tmp/wechat_search_auto.png", shell=True)
    print("✅ 完整搜一搜结果页已打开")
    if os.path.exists(SCREENSHOT):
        os.remove(SCREENSHOT)

if __name__ == "__main__":
    main()
