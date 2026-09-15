#!/bin/bash
# 视频号捕获工具一键启动脚本
# 用法: ./start-capture.sh [输出文件] [端口]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_FILE="${1:-videos.json}"
PORT="${2:-8899}"

echo "========================================"
echo "  视频号捕获工具 - 一键启动"
echo "========================================"

# 检查可执行文件
if [ ! -f "./video-capture" ]; then
    echo "未找到 video-capture，正在编译..."
    export GOPROXY=https://goproxy.cn,direct
    go build -o video-capture .
    echo "编译完成"
fi

# 检查CA证书是否已信任
if [ ! -f "ca.crt" ]; then
    echo "首次运行，将自动生成CA证书"
    echo "启动后请手动信任 ca.crt 证书"
fi

# 设置系统代理
echo "设置系统代理为 127.0.0.1:$PORT ..."
NETWORK_SERVICE=$(networksetup -listallnetworkservices | grep -v "An asterisk" | head -1)
networksetup -setwebproxy "$NETWORK_SERVICE" 127.0.0.1 "$PORT" 2>/dev/null || true
networksetup -setsecurewebproxy "$NETWORK_SERVICE" 127.0.0.1 "$PORT" 2>/dev/null || true

echo ""
echo "代理已设置，启动捕获工具..."
echo "输出文件: $OUTPUT_FILE"
echo "按 Ctrl+C 停止（停止后会自动关闭系统代理）"
echo "========================================"
echo ""

# 捕获退出信号，关闭代理
cleanup() {
    echo ""
    echo "正在关闭系统代理..."
    networksetup -setwebproxystate "$NETWORK_SERVICE" off 2>/dev/null || true
    networksetup -setsecurewebproxystate "$NETWORK_SERVICE" off 2>/dev/null || true
    echo "代理已关闭"
}
trap cleanup EXIT

# 启动捕获工具
./video-capture -port "$PORT" -output "$OUTPUT_FILE"
