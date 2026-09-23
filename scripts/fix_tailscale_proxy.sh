#!/usr/bin/env bash
# fix_tailscale_proxy.sh — 清除 Tailscale 网络服务上残留的本机代理
#
# 背景：早期探针会对"所有有 IP 的服务"（含 Tailscale 的 utun）设置代理，
#   探针停止时若 Tailscale 已关闭则漏清，在 Tailscale 服务上留下指向
#   127.0.0.1:8899 的"死代理"，导致开启 Tailscale 时可能断网。
#
# 关键：networksetup 只能在 Tailscale【正在运行】（utun 激活）时修改其代理；
#   Tailscale stopped 时执行会报 exit=5 "command not recognized"。
#
# 用法：
#   1) 先启动 Tailscale（菜单栏图标 → 启动/登录，状态为 connected）
#   2) bash scripts/fix_tailscale_proxy.sh
set -euo pipefail

SVC="Tailscale"

state="$(tailscale status --json 2>/dev/null | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("BackendState",""))
except Exception: print("")' 2>/dev/null || true)"

if [ "$state" != "Running" ]; then
  echo "Tailscale 当前未运行（BackendState=${state:-未知}）。" >&2
  echo "请先启动 Tailscale（菜单栏图标 → 启动），等它 connected 后再运行本脚本。" >&2
  exit 1
fi

sudo networksetup -setwebproxystate "$SVC" off
sudo networksetup -setsecurewebproxystate "$SVC" off

echo "已清除 Tailscale 服务代理，当前状态："
echo -n "  HTTP : "; networksetup -getwebproxy "$SVC"  | grep Enabled
echo -n "  HTTPS: "; networksetup -getsecurewebproxy "$SVC" | grep Enabled
