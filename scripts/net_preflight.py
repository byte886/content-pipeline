#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net_preflight.py — 跨机器、只读的网络环境预检与上游代理选择

【严格只读】不修改任何系统网络配置：不 set/state proxy、不改 pf/route、不杀进程、
不连接/断开 VPN。只做探测，输出 JSON：默认路由 / 代理端口及其"国内/翻墙"能力 /
Tailscale 状态 / （可选增强）物理网络服务明细，并给出确定性的推荐 upstream。

设计：核心决策【不依赖 networksetup】（系统网络框架异常时 networksetup 会挂死）：
  · 默认路由：route get / ip route
  · 代理能力：TCP 连通 + 经该端口实测国内/外网（socket/urllib，短超时）
  · Tailscale：pgrep 进程 + ifconfig（不调用会挂死的 tailscale CLI）
 依赖 networksetup / tailscale CLI 的"物理服务明细、Tailscale 服务残留"作为
【硬时间预算内的可选增强】，超时即降级并明确告警，绝不拖垮整个预检。

目的：采集会把系统代理临时指向本地 MITM 探针，预检在动手前判断"国内是否通、
是否有能翻墙的上游、Tailscale 是否冲突"，把"用不用代理、用哪个"变成配置驱动的
确定性结论，且不绑定某一台机器。

平台：macOS 完整；Linux 实现默认路由/端口探测/进程检测；Windows 仅端口探测，
其余标注未实现（不假装）。

配置（端口候选/直连域名/测试 URL/超时），后者覆盖前者：
  1. 环境变量 MCP_NET_CONFIG 指定文件
  2. ~/.config/multiplatform-content-pipeline/network.json（机器级覆盖）
  3. <仓库>/config/network.json（随仓默认）
  4. 本脚本内置 DEFAULT_NET_CONFIG（兜底）

用法:
  python3 scripts/net_preflight.py                  # 完整 JSON
  python3 scripts/net_preflight.py --upstream-only  # 只打印推荐 upstream（编排用）
  python3 scripts/net_preflight.py -o report.json   # 同时写文件
"""
import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NET_CONFIG = {
    "proxy_scheme": "http",
    "bind_host": "127.0.0.1",
    "proxy_port_candidates": [7890, 7897, 1087, 1080, 8889, 8080],
    "direct_domains": ["qq.com", "qpic.cn", "weixin.com"],
    "test": {
        "domestic_url": "https://www.baidu.com",
        "foreign_url": "https://www.gstatic.com/generate_204",
        "foreign_expect": 204,
        "tcp_timeout": 0.6,
        "domestic_timeout": 5,
        "foreign_timeout": 6,
    },
    "tailscale": {"cli": "tailscale", "cli_timeout": 3, "service_prefix": "tailscale"},
    "decision": {"prefer_foreign_proxy": True},
    "enhance_budget": 8.0,
}


# ── 配置加载 ────────────────────────────────────────────────────────────
def deep_merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_NET_CONFIG))
    paths = []
    env = os.environ.get("MCP_NET_CONFIG")
    if env:
        paths.append(Path(env))
    paths.append(Path.home() / ".config" / "multiplatform-content-pipeline" / "network.json")
    paths.append(REPO_ROOT / "config" / "network.json")
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                deep_merge(cfg, json.load(f))
        except FileNotFoundError:
            continue
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  忽略网络配置 {p}: {e}", file=sys.stderr)
    return cfg


# ── 通用：带超时执行外部命令（不挂死）────────────────────────────────────
def run_cmd(args, timeout=5):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError:
        return 127, "", "not found"


def parse_proxy_state(text):
    st = {"enabled": False, "server": None, "port": None}
    for line in text.splitlines():
        l = line.strip()
        if l.startswith("Enabled:"):
            st["enabled"] = "Yes" in l
        elif l.startswith("Server:"):
            st["server"] = l.split(":", 1)[1].strip() or None
        elif l.startswith("Port:"):
            try:
                st["port"] = int(l.split(":", 1)[1].strip())
            except ValueError:
                st["port"] = None
    return st


# ── 核心：默认路由（不依赖 networksetup）─────────────────────────────────
def default_route():
    sysname = platform.system()
    if sysname == "Darwin":
        _, out, _ = run_cmd(["route", "-n", "get", "default"], timeout=3)
        r = {}
        for l in out.splitlines():
            l = l.strip()
            if l.startswith("gateway:"):
                r["gateway"] = l.split(":", 1)[1].strip()
            elif l.startswith("interface:"):
                r["interface"] = l.split(":", 1)[1].strip()
        return r
    if sysname == "Linux":
        _, out, _ = run_cmd(["ip", "-o", "route", "show", "default"], timeout=3)
        r, toks = {}, out.split()
        if "via" in toks:
            r["gateway"] = toks[toks.index("via") + 1]
        if "dev" in toks:
            r["interface"] = toks[toks.index("dev") + 1]
        return r
    return {"note": "默认路由探测未在该平台实现"}


# ── 核心：代理端口探测与能力实测（不依赖 networksetup）───────────────────
def tcp_open(host, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def url_via_proxy(proxy_url, url, timeout):
    ph = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    op = urllib.request.build_opener(ph)
    req = urllib.request.Request(url, headers={"User-Agent": "net-preflight/1"})
    try:
        resp = op.open(req, timeout=timeout)
        return getattr(resp, "status", 200)
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def probe_candidates(cfg):
    t, host, out = cfg["test"], cfg["bind_host"], []
    for port in cfg["proxy_port_candidates"]:
        c = {"port": port, "tcp": False, "domestic_ok": False,
             "foreign_ok": False, "domestic_code": None, "foreign_code": None}
        if tcp_open(host, port, t["tcp_timeout"]):
            c["tcp"] = True
            purl = f"{cfg['proxy_scheme']}://{host}:{port}"
            dc = url_via_proxy(purl, t["domestic_url"], t["domestic_timeout"])
            c["domestic_code"], c["domestic_ok"] = dc, dc is not None and 200 <= dc < 400
            fc = url_via_proxy(purl, t["foreign_url"], t["foreign_timeout"])
            c["foreign_code"] = fc
            c["foreign_ok"] = (fc == t["foreign_expect"]) if t["foreign_expect"] \
                else (fc is not None and 200 <= fc < 400)
        out.append(c)
    return out


# ── 核心：Tailscale 快速检测（pgrep + ifconfig，不调用挂死的 CLI）────────
def quick_tailscale(cfg):
    tscfg = cfg["tailscale"]
    installed = shutil.which(tscfg["cli"]) is not None
    running = False
    if platform.system() != "Windows":
        code, out, _ = run_cmd(["pgrep", "-fl", "ailscale"], timeout=2)
        if code == 0:
            running = any(("ailscaled" in l) or ("tailscale" in l.lower())
                          for l in out.splitlines())
    state = "running" if running else ("stopped" if installed else "not_installed")
    return {"state": state, "installed": installed, "running": running}


# ── 增强：networksetup 明细 + tailscale CLI，硬预算内、超时降级 ───────────
def enhance_network(cfg, budget=None):
    budget = cfg.get("enhance_budget", 8.0) if budget is None else budget
    start, deadline = time.time(), time.time() + budget

    def rem():
        return max(0.15, deadline - time.time())

    def q(args, cap=2.0):
        return run_cmd(args, timeout=min(cap, rem()))

    detail, ts_extra, degraded = [], {}, False

    if platform.system() == "Darwin":
        code, hw, _ = q(["networksetup", "-listallhardwareports"])
        if code != 0:
            return detail, ts_extra, True  # 首个调用就挂：系统网络框架异常，快速降级
        dev = {}
        for b in hw.split("\n\n"):
            name = mac = device = None
            for line in b.splitlines():
                l = line.strip()
                if l.startswith("Hardware Port:"):
                    name = l.split(":", 1)[1].strip()
                elif l.startswith("Ethernet Address:"):
                    mac = l.split(":", 1)[1].strip()
                elif l.startswith("Device:"):
                    device = l.split(":", 1)[1].strip()
            if device:
                dev[device] = {"name": name,
                               "mac": (mac if mac and mac != "N/A" else None)}

        code, svcs, _ = q(["networksetup", "-listnetworkservices"])
        if code != 0:
            return detail, ts_extra, True
        names = [l.lstrip("* ").strip() for l in svcs.splitlines() if l.strip()]
        ts_service = next((s for s in names
                           if s.lower().startswith(cfg["tailscale"]["service_prefix"])), None)
        for s in names:
            if time.time() > deadline:
                degraded = True
                break
            _, info, _ = q(["networksetup", "-getinfo", s])
            device = next((l.split(":", 1)[1].strip() for l in info.splitlines()
                           if l.strip().startswith("Device:")), None)
            if not device or device not in dev or not dev[device]["mac"]:
                continue  # 无硬件 MAC = 虚拟/未连接（Tailscale utun 在此过滤）
            _, http, _ = q(["networksetup", "-getwebproxy", s])
            _, https, _ = q(["networksetup", "-getsecurewebproxy", s])
            detail.append({"name": s, "device": device, "mac": dev[device]["mac"],
                           "http": parse_proxy_state(http),
                           "https": parse_proxy_state(https)})
        if ts_service:
            _, https, _ = q(["networksetup", "-getsecurewebproxy", ts_service])
            ts_extra["service_name"] = ts_service
            ts_extra["service_proxy"] = parse_proxy_state(https)

    # tailscale CLI（预算内、超时强杀，daemon 停止时不挂死）
    cli = cfg["tailscale"]["cli"]
    if shutil.which(cli) and time.time() < deadline:
        try:
            p = subprocess.Popen([cli, "status", "--json"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                outb, _ = p.communicate(timeout=min(2.5, rem()))
                try:
                    ts_extra["cli"] = json.loads(outb).get("BackendState", "?")
                except json.JSONDecodeError:
                    ts_extra["cli"] = "cli_unparseable"
            except subprocess.TimeoutExpired:
                p.kill()
                p.communicate()
                ts_extra["cli"] = "cli_timeout"
        except FileNotFoundError:
            pass

    return detail, ts_extra, degraded


# ── 确定性决策（规则来自配置，非 AI 临场判断）────────────────────────────
def decide(cfg, candidates, tailscale):
    warnings = []
    foreign = [c for c in candidates if c["foreign_ok"]]
    tcp_up = [c for c in candidates if c["tcp"]]

    upstream = ""
    if cfg["decision"].get("prefer_foreign_proxy") and foreign:
        upstream = f"{cfg['proxy_scheme']}://{cfg['bind_host']}:{foreign[0]['port']}"
    elif tcp_up:
        warnings.append("本地代理端口在监听，但翻墙测试失败（节点失效/订阅过期）；"
                        "采集期间外网可能中断，请先切换节点或更新订阅。")
    else:
        warnings.append("未检测到本地代理：仅可国内采集；采集期间其他程序外网不可用。")

    sp = tailscale.get("service_proxy")
    if sp and sp.get("enabled"):
        warnings.append(f"Tailscale 服务残留代理（{sp.get('server')}:{sp.get('port')}）；"
                        "请在 Tailscale 运行时执行 scripts/fix_tailscale_proxy.sh 清理。")
    if tailscale.get("state") == "running":
        warnings.append("Tailscale 运行中：流量走 utun 点对点、不经系统代理，探针不影响。")

    return {"upstream": upstream, "vpn_ok": bool(foreign),
            "direct_domains": cfg["direct_domains"], "warnings": warnings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-only", action="store_true",
                    help="只打印推荐 upstream URL（空串=直连）")
    ap.add_argument("-o", "--out", help="完整 JSON 同时写入该文件")
    args = ap.parse_args()

    cfg = load_config()
    sysname = platform.system()

    candidates = probe_candidates(cfg)          # 核心：代理能力
    tailscale = quick_tailscale(cfg)            # 核心：Tailscale 进程
    detail, ts_extra, degraded = enhance_network(cfg)  # 增强：预算内
    tailscale.update(ts_extra)
    recommendation = decide(cfg, candidates, tailscale)
    if degraded:
        recommendation["warnings"].insert(
            0, "系统网络框架（networksetup）无响应或缓慢（系统网络层可能异常）；"
               "结论基于端口直连探测，未读取网络服务明细。")

    net_services = detail if detail else \
        [{"note": f"未获取网络服务明细（{sysname} 或 networksetup 不可用/超时）"}]

    report = {
        "schema": "net-preflight/1",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "platform": sysname,
        "hostname": platform.node(),
        "default_route": default_route(),
        "network_services": net_services,
        "proxy_candidates": candidates,
        "tailscale": tailscale,
        "recommendation": recommendation,
    }

    if args.upstream_only:
        print(recommendation["upstream"])
        return

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    for w in recommendation["warnings"]:
        print(f"⚠️  {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
