#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""incremental_sync.py — 方案A 视频号增量对账与差集下载

再次捕获全量后，把"新捕获的 signed manifest"与"已落库 inventory 台账"按稳定
唯一键 id（16 位 hex，= md5(md5sum)[:16]，三处口径一致）对账，只把差集（新增）
交给 batch_download_v4.py 下载，不重复下载已有内容。

入参约定：
  capture   ：parse_capture_log.py 产出的【signed manifest】（含 url/decode_key，
              票据几小时有效），顶层含 shorts / replays 两个数组。
              ⚠️ 不是脱敏 catalog（脱敏件无 url/decode_key，无法下载）。
  inventory ：rebuild_inventory.py 产出的台账，顶层含 shorts / lives，条目主键 id。

用法:
  python3 incremental_sync.py <signed_manifest.json> <inventory.json> \
        [--outdir DIR] [--quality min|default|max] [--apply]

  不带 --apply：只 dry-run 对账，打印 已有/新增/过滤，写出 missing_*.json 差集清单。
  带  --apply：对账后调用 batch_download_v4.py 下载差集（短视频解密在下载器内完成）。

职责边界：本脚本【不手写台账】。下载（及转写）完成后，统一运行
  batch_transcribe.py → rebuild_inventory.py → audit_disk.py
重建台账与对账，保证时长/转写/校验门口径唯一。

过滤规则（不下载）：
  - 图文动态：duration<=0，或短视频缺 decode_key（短视频 Isaac64 加密需解码密钥；
    回放为明文 MP4，不要求 decode_key）。
"""
import sys, json, argparse, subprocess
from pathlib import Path


def load(p):
    return json.load(open(p, encoding="utf-8"))


def is_skip(item, require_decode_key):
    """图文/不可播放动态过滤。短视频要求 decode_key（Isaac64 解密），回放明文不要求。"""
    if (item.get("duration") or 0) <= 0:
        return True
    if require_decode_key and not item.get("decode_key"):
        return True
    return False


def diff_section(cap_list, inv_list, require_decode_key):
    """返回 (新增条目, 已有数, 过滤数)。主键统一 id。"""
    have = {x.get("id") for x in inv_list if x.get("id")}
    new, filtered, dup = [], 0, 0
    seen = set()
    for it in cap_list:
        i = it.get("id")
        if not i or i in seen:
            continue
        seen.add(i)
        if is_skip(it, require_decode_key):
            filtered += 1
            continue
        if i in have:
            dup += 1
        else:
            new.append(it)
    return new, dup, filtered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", help="新捕获的 signed manifest（含 url/decode_key）")
    ap.add_argument("inventory", help="已落库 inventory 台账")
    ap.add_argument("--outdir", default=None,
                    help="差集清单与（--apply 时）视频输出目录；dry-run 默认当前目录")
    ap.add_argument("--quality", default="min", choices=["min", "default", "max"])
    ap.add_argument("--apply", action="store_true", help="下载差集")
    a = ap.parse_args()

    cap = load(a.capture)
    inv = load(a.inventory)

    new_s, dup_s, filt_s = diff_section(
        cap.get("shorts", []), inv.get("shorts", []), require_decode_key=True)
    new_r, dup_r, filt_r = diff_section(
        cap.get("replays", []), inv.get("lives", []), require_decode_key=False)

    print(f"短视频: 已有 {dup_s} | 新增 {len(new_s)} | 过滤 {filt_s}")
    print(f"直播回放: 已有 {dup_r} | 新增 {len(new_r)} | 过滤 {filt_r}")

    if not new_s and not new_r:
        print("✅ 无新增，台账已是最新。")
        return

    outdir = Path(a.outdir) if a.outdir else Path(".")
    outdir.mkdir(parents=True, exist_ok=True)
    base = Path(a.capture).stem
    miss_s = outdir / f"missing_short_{base}.json"
    miss_r = outdir / f"missing_live_{base}.json"
    json.dump(new_s, open(miss_s, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(new_r, open(miss_r, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"差集清单: {miss_s} ({len(new_s)}) / {miss_r} ({len(new_r)})")

    if not a.apply:
        print("dry-run，未下载。确认后加 --apply 执行下载。")
        return

    if not a.outdir:
        sys.exit("--apply 必须用 --outdir 指定视频输出根目录（其下需有 short/live 子目录）")

    dl = Path(__file__).parent / "batch_download_v4.py"
    # 序号在现有台账最大值后续接
    start_short = max((x.get("seq", 0) for x in inv.get("shorts", [])), default=0) + 1
    start_live = max((x.get("seq", 0) for x in inv.get("lives", [])), default=0) + 1
    for tag, miss_json, start in [
        ("short", miss_s, start_short),
        ("live", miss_r, start_live),
    ]:
        items = json.load(open(miss_json, encoding="utf-8"))
        if not items:
            continue
        section_dir = outdir / ("short" if tag == "short" else "live")
        section_dir.mkdir(parents=True, exist_ok=True)
        print(f"→ 下载 {tag} 新增 {len(items)} 条，序号从 {start}，输出 {section_dir}")
        subprocess.run([sys.executable, str(dl), str(miss_json), str(section_dir),
                        tag, str(start), a.quality], check=True)

    print("\n✅ 差集下载完成。接下来请运行：")
    print("  1) batch_transcribe.py <视频根> <转写根>   # 新增视频转写")
    print("  2) rebuild_inventory.py ...                # 用新全量 catalog 重建台账")
    print("  3) audit_disk.py ...                       # 文件盘对账至全 0")


if __name__ == "__main__":
    main()
