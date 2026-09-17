#!/bin/bash
# 股票知识库目录同步到百度网盘
#
# 用法:
#   bash scripts/netdisk/sync_stock.sh <本地子目录> <网盘子目录> [并发数=2]
#
# 示例:
#   bash scripts/netdisk/sync_stock.sh "01_video/stock/交易的游戏/short" "01_video/stock/交易的游戏/short"
#   bash scripts/netdisk/sync_stock.sh "06_articles/stock/顶底之王" "06_articles/stock/顶底之王"
#
# 特性:
#   - 递归上传目录下所有文件
#   - 断点续传：已上传的文件跳过（通过网盘文件列表判断）
#   - 并发上传（默认2）
#   - 大文件分片上传，MD5秒传

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_DIR"

LOCAL_SUBDIR="$1"
REMOTE_SUBDIR="$2"
PARALLEL="${3:-2}"
export BAIDU_ENC_PASS="***REMOVED***"

LOCAL_BASE="$PROJECT_DIR/library/$LOCAL_SUBDIR"
REMOTE_BASE="/apps/CPA课程归档/股票知识库/$REMOTE_SUBDIR"

if [ ! -d "$LOCAL_BASE" ]; then
    echo "错误：本地目录不存在: $LOCAL_BASE"
    exit 1
fi

echo "============================================"
echo " 股票知识库同步网盘"
echo " 本地: $LOCAL_BASE"
echo " 网盘: $REMOTE_BASE"
echo " 并发: $PARALLEL"
echo " 开始: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 确保网盘目录存在
BAIDU_ENC_PASS=***REMOVED*** python3 "$SCRIPT_DIR/baidu_upload.py" mkdir "$REMOTE_BASE" 2>/dev/null

# 统计文件数
TOTAL=$(find -L "$LOCAL_BASE" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "待上传文件: $TOTAL 个"
echo ""

# 并发上传
upload_file() {
    local rel_path="$1"
    local local_file="$LOCAL_BASE/$rel_path"
    local remote_file="$REMOTE_BASE/$rel_path"
    
    # 确保网盘子目录存在
    local remote_dir=$(dirname "$remote_file")
    BAIDU_ENC_PASS=***REMOVED*** python3 "$SCRIPT_DIR/baidu_upload.py" mkdir "$remote_dir" 2>/dev/null
    
    # 上传
    if BAIDU_ENC_PASS=***REMOVED*** python3 "$SCRIPT_DIR/baidu_upload.py" upload "$local_file" "$remote_file" 2>&1 | tail -1; then
        echo "[OK] $rel_path"
    else
        echo "[FAIL] $rel_path"
    fi
}
export -f upload_file
export LOCAL_BASE REMOTE_BASE SCRIPT_DIR

# 列出所有文件，并发上传
find -L "$LOCAL_BASE" -type f 2>/dev/null | while read f; do
    echo "${f#$LOCAL_BASE/}"
done | xargs -P "$PARALLEL" -I{} bash -c 'upload_file "$@"' _ {}

echo ""
echo "============================================"
echo " 同步完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
