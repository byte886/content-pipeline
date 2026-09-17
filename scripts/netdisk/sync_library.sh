#!/bin/bash
# 通用知识库目录同步到百度网盘
#
# 用法:
#   bash scripts/netdisk/sync_library.sh <知识库名> <本地子目录> <网盘子目录> [并发数=1]
#
# 示例:
#   bash scripts/netdisk/sync_library.sh "股票知识库" "01_video/stock/交易的游戏/short" "01_video/stock/交易的游戏/short"
#   bash scripts/netdisk/sync_library.sh "珠宝知识库" "01_video/jewelry/宝石学家老许" "01-视频原片"
#
# 特性:
#   - 递归上传目录下所有文件（正确处理中文/空格/特殊字符文件名）
#   - 断点续传：已上传的文件跳过（通过网盘文件列表判断）
#   - 单线程顺序上传（大文件场景更可靠，默认并发1）
#   - 大文件分片上传，MD5秒传

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_DIR"

KB_NAME="$1"
LOCAL_SUBDIR="$2"
REMOTE_SUBDIR="$3"
PARALLEL="${4:-1}"
export BAIDU_ENC_PASS="***REMOVED***"

LOCAL_BASE="$PROJECT_DIR/library/$LOCAL_SUBDIR"
REMOTE_BASE="/apps/CPA课程归档/$KB_NAME/$REMOTE_SUBDIR"

if [ ! -d "$LOCAL_BASE" ]; then
    echo "错误：本地目录不存在: $LOCAL_BASE"
    exit 1
fi

echo "============================================"
echo " $KB_NAME 同步网盘"
echo " 本地: $LOCAL_BASE"
echo " 网盘: $REMOTE_BASE"
echo " 并发: $PARALLEL"
echo " 开始: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 统计文件数
TOTAL=$(find -L "$LOCAL_BASE" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "待上传文件: $TOTAL 个"
echo ""

COUNT=0
FAIL=0

# 用NUL分隔符正确处理中文/空格/特殊字符文件名
find -L "$LOCAL_BASE" -type f -print0 2>/dev/null | while IFS= read -r -d '' local_file; do
    rel_path="${local_file#$LOCAL_BASE/}"
    remote_file="$REMOTE_BASE/$rel_path"
    remote_dir=$(dirname "$remote_file")
    
    COUNT=$((COUNT + 1))
    
    # 确保网盘子目录存在（mkdir已存在会返回31064，忽略）
    BAIDU_ENC_PASS=***REMOVED*** python3 "$SCRIPT_DIR/baidu_upload.py" mkdir "$remote_dir" 2>/dev/null
    
    # 上传
    if BAIDU_ENC_PASS=***REMOVED*** python3 "$SCRIPT_DIR/baidu_upload.py" upload "$local_file" "$remote_file" 2>&1 | grep -q "Done! fs_id"; then
        echo "[OK $COUNT/$TOTAL] $rel_path"
    else
        echo "[FAIL $COUNT/$TOTAL] $rel_path"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "============================================"
echo " 同步完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo " 总计: $TOTAL, 失败: $FAIL"
echo "============================================"
