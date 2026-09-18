#!/bin/bash
# 安全停止video-capture：先发送SIGTERM让进程恢复代理，超时后再强制杀死
set -e

PORT=8899
PID_FILE=/tmp/video_capture_pid.txt

echo "=== 停止video-capture ==="

# 方法1: 通过PID文件
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "发送SIGTERM到进程 $PID (允许恢复系统代理)..."
        kill "$PID"
        
        # 等待最多5秒让进程正常退出
        for i in {1..5}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                echo "进程已正常退出"
                rm -f "$PID_FILE"
                break
            fi
            sleep 1
        done
        
        # 如果还在运行，强制杀死
        if kill -0 "$PID" 2>/dev/null; then
            echo "进程未响应，强制杀死..."
            kill -9 "$PID"
            # 手动恢复代理
            echo "手动恢复系统代理..."
            networksetup -setwebproxystate "Wi-Fi" off 2>/dev/null || true
            networksetup -setsecurewebproxystate "Wi-Fi" off 2>/dev/null || true
        fi
    else
        echo "进程 $PID 未运行"
    fi
    rm -f "$PID_FILE"
fi

# 方法2: 通过端口查找
PID=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$PID" ]; then
    echo "端口 $PORT 仍被进程 $PID 占用，发送SIGTERM..."
    kill "$PID" 2>/dev/null || true
    sleep 2
    if lsof -ti:$PORT >/dev/null 2>&1; then
        echo "强制杀死..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    fi
fi

# 验证代理状态
echo ""
echo "=== 验证系统代理状态 ==="
HTTP_ENABLED=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null | grep "Enabled" | awk '{print $2}')
echo "Wi-Fi HTTP代理: $HTTP_ENABLED"

# 如果代理还指向8899，手动关闭
if networksetup -getwebproxy "Wi-Fi" 2>/dev/null | grep -q "Port: 8899"; then
    echo "检测到代理仍指向8899，手动关闭..."
    networksetup -setwebproxystate "Wi-Fi" off
    networksetup -setsecurewebproxystate "Wi-Fi" off
    echo "已关闭Wi-Fi代理"
fi

echo ""
echo "=== 停止完成 ==="
