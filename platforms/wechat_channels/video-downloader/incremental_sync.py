#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""incremental_sync.py — 方案A 视频号增量对账

再次滚动捕获后，把新捕获 manifest 与已落库台账按 encfilekey(=捕获id) 对账，
只产出"新增"清单交给现有下载脚本，不重复下载。

用法:
  python3 incremental_sync.py <新捕获manifest.json> <inventory.json> \
        [--outdir DIR] [--quality min|default|max] [--apply]

  不带 --apply：只 dry-run 对账，打印新增/已有/缺失统计，写出 missing_*.json
  带  --apply：对账后调用 batch_download_v4.py 下载差集，并把新条目追加进 inventory

约定:
  - 稳定唯一键 = encfilekey（捕获产物里叫 id，16位hex）
  - 图文动态（无 decode_key / mediaType=2 / duration=0）自动过滤，不下载
"""
import sys, json, argparse, subprocess, os
from pathlib import Path

def load(p):
    return json.load(open(p, encoding="utf-8"))

def known_ids(inv, key):
    return {x["encfilekey"] for x in inv.get(key, []) if x.get("encfilekey")}

def is_skip(item, require_decode_key):
    """过滤图文动态。短视频才要求 decode_key（回放是明文MP4，无 decode_key，不过滤）"""
    if require_decode_key and not item.get("decode_key"):
        return True
    if (item.get("duration") or 0) <= 0:
        return True
    return False

def diff_section(cap_list, inv_list, require_decode_key):
    have = {x["encfilekey"] for x in inv_list if x.get("encfilekey")}
    new, filtered = [], 0
    dup = 0
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
    ap.add_argument("capture")
    ap.add_argument("inventory")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--quality", default="min")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cap = load(a.capture)
    inv = load(a.inventory)

    new_s, dup_s, filt_s = diff_section(cap.get("shorts", []), inv.get("shorts", []), require_decode_key=True)
    new_r, dup_r, filt_r = diff_section(cap.get("replays", []), inv.get("lives", []), require_decode_key=False)

    print(f"短视频: 已有 {dup_s} | 新增 {len(new_s)} | 过滤图文 {filt_s}")
    print(f"直播回放: 已有 {dup_r} | 新增 {len(new_r)} | 过滤图文 {filt_r}")

    if not new_s and not new_r:
        print("✅ 无新增，台账已是最新。")
        return

    # 写差集清单
    base = Path(a.capture).stem
    miss_s = Path(f"missing_short_{base}.json")
    miss_r = Path(f"missing_live_{base}.json")
    json.dump(new_s, open(miss_s, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(new_r, open(miss_r, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"差集清单: {miss_s} ({len(new_s)}) / {miss_r} ({len(new_r)})")

    if not a.apply:
        print("dry-run，未下载。确认后加 --apply 执行。")
        return

    # 下载 + 台账续接（调用现有下载脚本，序号续接）
    dl = Path(__file__).parent / "batch_download_v4.py"
    for tag, miss_json, cur_list, outdir in [
        ("short", miss_s, inv["shorts"], a.outdir),
        ("live", miss_r, inv["lives"], a.outdir),
    ]:
        if not miss_json.exists() or len(json.load(open(miss_json))) == 0:
            continue
        start_seq = max((x["seq"] for x in cur_list), default=0) + 1
        subprocess.run([sys.executable, str(dl), str(miss_json), str(outdir),
                        tag, str(start_seq), a.quality], check=True)
        # 追加台账（encfilekey 回填为捕获 id）
        for it in json.load(open(miss_json)):
            cur_list.append({
                "seq": start_seq,
                "file": f"{tag}_{start_seq}_{it.get('short_title','')}.mp4",
                "title": it.get("short_title"),
                "duration_s": it.get("duration"),
                "disk_size_mb": round((it.get("size") or 0) / 1048576, 1),
                "encfilekey": it.get("id"),
            })
            start_seq += 1
    inv["summary"]["short_total"] = len(inv["shorts"])
    inv["summary"]["live_total"] = len(inv["lives"])
    json.dump(inv, open(a.inventory, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 已下载并更新台账: {a.inventory}")

if __name__ == "__main__":
    main()
