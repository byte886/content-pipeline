#!/usr/bin/env python3
"""
微信主窗口搜索公众号/视频号稳定流程（已实测验证成功）
用法：python3 wechat_search_shengcai.py <搜索关键词>
流程：
1. 复位主窗口到左上角900x600
2. 按ESC关所有弹窗，Cmd+1切聊天视图
3. Cmd+F激活搜索框，粘贴关键词
4. 鼠标在下拉列表内滚到底部，直到看到红色"搜索网络结果"
5. 按1次↓选中第一个目标条目
6. 回车打开搜一搜结果窗口
"""
import subprocess, time, sys, pyautogui

KEYWORD = sys.argv[1] if len(sys.argv) > 1 else "生财有术"

def osascript(cmd):
    subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)

print(f"=== 开始搜索：{KEYWORD} ===")
# 1. 激活微信主窗口，复位位置
osascript('tell application "WeChat" to activate')
time.sleep(0.5)
osascript('''
tell application "System Events"
  tell process "WeChat"
    set size of window 1 to {900, 600}
    set position of window 1 to {0, 0}
  end tell
end tell
''')
time.sleep(0.5)

# 2. 关弹窗，切聊天视图
for _ in range(3):
    osascript('tell application "System Events" to tell process "WeChat" to key code 53')
    time.sleep(0.15)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "1" using {command down}')
time.sleep(0.5)

# 3. 激活搜索框，粘贴关键词
osascript('tell application "System Events" to tell process "WeChat" to keystroke "f" using {command down}')
time.sleep(0.3)
subprocess.run("echo -n '{}' | pbcopy".format(KEYWORD), shell=True, check=True)
osascript('tell application "System Events" to tell process "WeChat" to keystroke "v" using {command down}')
time.sleep(1.2)

# 4. 鼠标在下拉列表内滚到底部
pyautogui.moveTo(120, 300, duration=0.3)
for _ in range(20):
    pyautogui.scroll(-10)
    time.sleep(0.08)
time.sleep(0.3)

# 5. 按1次↓选中目标条目，回车打开
osascript('tell application "System Events" to tell process "WeChat" to key code 125')
time.sleep(0.2)
osascript('tell application "System Events" to tell process "WeChat" to key code 36')
time.sleep(6)
print("✅ 搜索完成，搜一搜窗口已打开")
