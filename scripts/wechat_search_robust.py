#!/usr/bin/env python3
import pyautogui, time, subprocess, sys, os
OCR_SCRIPT = "/Users/wenjiechen/Doubao/skills/work-doc-extract/scripts/ocr_vision.swift"
def osascript(cmd):
    subprocess.run(["osascript", "-e", cmd], check=False, capture_output=True)
def get_win_count():
    res = subprocess.run('osascript -e \'tell application "System Events" to tell process "WeChat" to count of windows\'', shell=True, capture_output=True, text=True).stdout.strip()
    try: return int(res)
    except: return 0

keyword = sys.argv[1] if len(sys.argv)>1 else "生财有术"
print(f"=== 开始搜索: {keyword} ===")
osascript('tell application "WeChat" to reopen')
time.sleep(1.5)
osascript('tell application "WeChat" to activate')
time.sleep(1)
for _ in range(10):
    if get_win_count() <=1: break
    osascript('tell application "System Events" to tell process "WeChat" to keystroke "w" using {command down}')
    time.sleep(0.5)
for _ in range(3):
    osascript('tell application "System Events" to tell process "WeChat" to key code 53')
    time.sleep(0.15)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "1" using {command down}')
time.sleep(0.3)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "f" using {command down}')
time.sleep(0.3)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "a" using {command down}')
time.sleep(0.1)
osascript('tell application "System Events" to tell process "WeChat" to key code 51')
time.sleep(0.1)
subprocess.run("pbcopy", input=keyword.encode(), check=True)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "v" using {command down}')
time.sleep(1.2)
pyautogui.moveTo(200,280,duration=0.3)
for i in range(25):
    pyautogui.scroll(-10)
    time.sleep(0.15)
    subprocess.run("screencapture -x -C /tmp/chk.png", shell=True, check=True)
    r = subprocess.run(["swift", OCR_SCRIPT, "/tmp/chk.png"], capture_output=True, text=True).stdout
    if "搜索网络" in r:
        print(f"✅ 第{i+1}次滚动到网络结果区")
        break
pyautogui.click(200,265)
time.sleep(0.3)
for _ in range(3):
    osascript('tell application "System Events" to tell process "WeChat" to key code 125')
    time.sleep(0.2)
osascript('tell application "System Events" to tell process "WeChat" to key code 36')
time.sleep(6)
subprocess.run("screencapture -x -C /tmp/search_success.png", shell=True, check=True)
print("✅ 搜索流程执行完成")
os.path.exists("/tmp/chk.png") and os.remove("/tmp/chk.png")
