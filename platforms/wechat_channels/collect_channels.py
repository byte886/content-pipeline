#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_channels.py — 微信视频号「人工一步」全量/增量采集编排（方案A）

把整条流水线串成一条命令：
  启动 captor(自动设系统代理) → 提示人工在微信打开视频号主页 → 轮询 all-done
  → 优雅停 captor(自动清代理) → parse 重组(catalog 脱敏 + signed 含票据)
  → 增量对账(只下新增) → 下载解密 → FunASR 转写 → 重建台账 → 文件盘对账

人机边界（重要）：
  微信是腾讯桌面客户端，其界面不允许 AI 自动化。本脚本【不碰微信 GUI】，
  唯一人工动作 = 在微信里搜索账号名 → 点「视频号」行进入主页（约 15 秒），
  此后枚举/翻页/换签/下载/解密/转写/台账全部自动。

仅 macOS（captor 的系统代理管理为 proxy_darwin.go）。

用法:
  python3 collect_channels.py <视频号名称> [--domain stock] [--quality min]
      [--upstream ""] [--capture-timeout 360] [--no-download] [--build]

  --quality   min(默认,知识型转文字)/default/max
  --upstream  auto(默认)=探测 ClashX 7890：在则外网链式转发、不在则直连；
              传 "" 强制直连，或显式 URL
  --no-download  只捕获+重组+对账打印，不下载/转写/重建
  --build     启动前先 go build 编译 captor
"""
import argparse
import glob
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 路径推导（不写死用户目录）──────────────────────────────────────────
HERE = Path(__file__).resolve().parent                 # platforms/wechat_channels
ROOT = HERE.parents[1]                                  # 仓库根
CAP_DIR = HERE / "video-capture"
DL_DIR = HERE / "video-downloader"
TR_DIR = HERE / "video-transcribe"
CAP_BIN = CAP_DIR / "video-capture"
PARSE = CAP_DIR / "parse_capture_log.py"
INCR = DL_DIR / "incremental_sync.py"
TRANSCRIBE = TR_DIR / "batch_transcribe.py"
REBUILD = DL_DIR / "rebuild_inventory.py"
AUDIT = DL_DIR / "audit_disk.py"

MANIFEST_DIR = ROOT / "library" / "00_manifest"
WORKSPACE_CAP = ROOT / "workspace" / "capture"
WORKSPACE_SIGNED = ROOT / "workspace" / "signed"

ALL_DONE_RE = re.compile(r'all-done","short":(\d+),"live":(\d+)')


def log(msg):
    print(f"[collect] {msg}", flush=True)


def run(cmd, **kw):
    """实时透传子进程输出。"""
    log("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def port_listening(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    ok = s.connect_ex(("127.0.0.1", port)) == 0
    s.close()
    return ok


def funasr_python():
    env = os.environ.get("FUNASR_PYTHON")
    if env and Path(env).exists():
        return env
    cand = Path.home() / ".venvs" / "funasr" / "bin" / "python"
    return str(cand) if cand.exists() else sys.executable


def clear_system_proxy_fallback(port):
    """captor 正常退出会自清代理（proxy_darwin.go 快照恢复）；这里仅在检测到
    某物理服务仍指向本端口时兜底关闭。Tailscale 等虚拟服务 stopped 时改不了
    （exit=5），跳过它，残留交给 scripts/fix_tailscale_proxy.sh。"""
    try:
        out = subprocess.run(["networksetup", "-listallnetworkservices"],
                             capture_output=True, text=True).stdout
        services = [l.lstrip("* ").strip() for l in out.splitlines()[1:] if l.strip()]
        for svc in services:
            if svc.lower().startswith("tailscale"):
                continue
            state = subprocess.run(["networksetup", "-getsecurewebproxy", svc],
                                   capture_output=True, text=True).stdout
            if f"{port}" in state and "Enabled: Yes" in state:
                log(f"⚠️  {svc} 代理仍指向 {port}，兜底关闭")
                subprocess.run(["networksetup", "-setwebproxystate", svc, "off"],
                               capture_output=True)
                subprocess.run(["networksetup", "-setsecurewebproxystate", svc, "off"],
                               capture_output=True)
    except FileNotFoundError:
        pass


def main():
    if sys.platform != "darwin":
        sys.exit("本采集器目前仅支持 macOS（系统代理管理为 proxy_darwin.go）。")

    ap = argparse.ArgumentParser()
    ap.add_argument("account", help="视频号名称，如 交易的游戏")
    ap.add_argument("--domain", default="stock", help="行业目录，如 stock/jewelry")
    ap.add_argument("--quality", default="min", choices=["min", "default", "max"])
    ap.add_argument("--upstream", default="auto",
                    help='auto(默认)=探测 ClashX 7890：在则链式转发外网、不在则直连；'
                         '传 "" 强制直连；或显式 URL 如 http://127.0.0.1:7890')
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--capture-timeout", type=int, default=360)
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()

    if a.upstream == "auto":
        clash = "http://127.0.0.1:7890"
        a.upstream = clash if port_listening(7890) else ""
        log(f"upstream=auto → {'ClashX 7890（外网链式转发，微信域名直连）' if a.upstream else '直连（未检测到 ClashX 7890）'}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_root = ROOT / "library" / "01_video" / a.domain / a.account
    transcript_root = ROOT / "library" / "04_transcript" / a.domain / a.account
    catalog_lib = MANIFEST_DIR / f"catalog_{a.account}.json"
    inventory_lib = MANIFEST_DIR / f"{a.account}_inventory.json"
    audit_lib = MANIFEST_DIR / f"audit_{a.account}.json"
    raw_json = WORKSPACE_CAP / f"{a.account}_{ts}.json"
    api_log = WORKSPACE_CAP / f"{a.account}_{ts}_api.log"
    signed_dir = WORKSPACE_SIGNED / f"{a.account}_{ts}"
    catalog_ws = WORKSPACE_CAP / f"{a.account}_{ts}_catalog.json"
    for d in (WORKSPACE_CAP, signed_dir, video_root / "short", video_root / "live",
              transcript_root / "short", transcript_root / "live", MANIFEST_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # 0) 编译 / 端口检查
    if a.build or not CAP_BIN.exists():
        log("编译 captor …")
        env = dict(os.environ, GOPROXY="https://goproxy.cn,direct")
        subprocess.run(["go", "build", "-o", "video-capture", "."],
                       cwd=str(CAP_DIR), env=env, check=True)
    if port_listening(a.port):
        sys.exit(f"端口 {a.port} 已被占用，可能已有 captor 在跑：先停止它（kill -TERM 监听者）。")

    # 1) 启动 captor（自动设系统代理）
    log(f"启动 captor :{a.port}（upstream={a.upstream or '直连'}）")
    cap = subprocess.Popen(
        [str(CAP_BIN), "-replay-list", "-short-probe",
         "-upstream", a.upstream, "-port", str(a.port),
         "-output", str(raw_json)],
        stdout=open(api_log, "ab"), stderr=subprocess.STDOUT)

    def cleanup(*_):
        if cap.poll() is None:
            log("停止 captor（SIGTERM，等待其自动清代理）…")
            cap.terminate()
            try:
                cap.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cap.kill()
            time.sleep(2)
            clear_system_proxy_fallback(a.port)

    signal.signal(signal.SIGINT, lambda *x: (cleanup(), sys.exit(130)))
    signal.signal(signal.SIGTERM, lambda *x: (cleanup(), sys.exit(143)))

    try:
        # 等代理端口就绪
        for _ in range(30):
            if port_listening(a.port):
                break
            time.sleep(0.5)
        else:
            cleanup()
            sys.exit("captor 端口未就绪，放弃。")
        log("✓ captor 已就绪，系统代理已设置")

        # 2) 人工一步
        print("\n" + "=" * 64)
        print(f"  请在【微信】里完成唯一一步（约 15 秒）：")
        print(f"   1. 搜索  「{a.account}」")
        print(f"   2. 点中  【视频号】 那一行进入主页（别点成公众号）")
        print(f"   3. 若之前开着该主页，请先彻底关掉窗口再重新进入")
        print(f"      （必须让主页 HTML 重新请求，注入才会生效）")
        print(f"   4. 不用滚动、不用点视频，静候自动跑完即可")
        print("=" * 64 + "\n")
        log("正在等待 all-done …（你可以现在去微信操作）")

        # 3) 轮询 all-done
        deadline = time.time() + a.capture_timeout
        last_feed = -1
        m = None
        while time.time() < deadline:
            if cap.poll() is not None:
                cleanup()
                sys.exit("captor 进程意外退出，请看日志：%s" % api_log)
            if api_log.exists():
                txt = api_log.read_text(errors="ignore")
                m = ALL_DONE_RE.search(txt)
                if m:
                    break
                feed = txt.count("RLIST_FEED")
                if feed != last_feed and feed:
                    log(f"…已重组 {feed} 个列表快照")
                    last_feed = feed
                errs = re.findall(r"RLIST_[A-Z_]*ERR[A-Z_]*", txt)
                if errs:
                    log("⚠️  注入报错: %s" % sorted(set(errs)))
            time.sleep(5)

        if not m:
            cleanup()
            sys.exit(f"⏱ 超时未捕获 all-done（{a.capture_timeout}s）。\n"
                     f"  常见原因：没点进【视频号】主页 / 旧窗口没重进导致未注入。\n"
                     f"  日志：{api_log}")
        short_n, live_n = int(m.group(1)), int(m.group(2))
        log(f"✓ all-done：短视频 {short_n}，直播回放 {live_n}")
    finally:
        cleanup()

    # 4) parse 重组（脱敏 catalog + 含票据 signed）
    log("重组捕获日志 …")
    run([sys.executable, PARSE, api_log, "--account", a.account,
         "--catalog-out", catalog_ws, "--signed-dir", signed_dir])
    manifests = sorted(glob.glob(str(signed_dir / "*_manifest_signed.json")))
    if not manifests:
        sys.exit("未生成 signed manifest，无法下载：%s" % signed_dir)
    signed_manifest = manifests[-1]

    # catalog 落库（备份旧版）
    if catalog_lib.exists():
        bak = WORKSPACE_CAP / f"{catalog_lib.stem}.bak.{ts}.json"
        shutil.copy2(catalog_lib, bak)
        log(f"旧 catalog 已备份: {bak.name}")
    shutil.copy2(catalog_ws, catalog_lib)
    log(f"catalog 已更新: {catalog_lib.relative_to(ROOT)}")

    if a.no_download:
        log("--no-download：到此为止（已捕获/重组/落 catalog，未下载）。")
        return

    # 5) 增量对账 + 下载差集
    first_time = not inventory_lib.exists()
    log("首次全量采集（无历史台账）。" if first_time else "增量对账 …")
    run([sys.executable, INCR, signed_manifest, inventory_lib,
         "--outdir", video_root, "--quality", a.quality, "--apply"])

    # 6) 转写（已转写自动跳过）
    py = funasr_python()
    log(f"转写（FunASR: {py}，已转写自动跳过）…")
    for sec in ("short", "live"):
        vd, td = video_root / sec, transcript_root / sec
        if list(vd.glob("*.mp4")):
            run([py, TRANSCRIBE, vd, td])

    # 7) 重建台账 + 对账
    log("重建台账 …")
    run([sys.executable, REBUILD,
         "--catalog", catalog_lib, "--video-root", video_root,
         "--transcript-root", transcript_root,
         "--domain", a.domain, "--out", inventory_lib])
    log("文件盘对账 …")
    run([sys.executable, AUDIT,
         "--catalog", catalog_lib, "--video-root", video_root, "--out", audit_lib])
    audit = __import__("json").load(open(audit_lib, encoding="utf-8"))
    for key, label in (("short", "短视频"), ("live", "直播回放")):
        x = audit.get(key, {})
        log(f"{label}: 全集{x.get('catalog_total')} 磁盘{x.get('disk_files')} "
            f"缺{x.get('missing_count')} 游离{x.get('orphan_count')} 歧义{x.get('ambiguous_count')}")

    print("\n" + "=" * 64)
    log("✅ 完成。")
    log(f"台账 {inventory_lib.relative_to(ROOT)}")
    log(f"对账 {audit_lib.relative_to(ROOT)}（缺/游离/歧义应为 0）")
    log(f"含票据清单在 {signed_dir.relative_to(ROOT)}（已 gitignore，确认无误可删）")
    print("=" * 64)


if __name__ == "__main__":
    main()
