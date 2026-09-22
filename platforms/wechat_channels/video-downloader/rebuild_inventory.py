#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_inventory.py — 以 catalog 的 16hex id 为主键，用 audit_disk 的严格匹配
（ffprobe 实测时长 + 归一化标题 + hashtag 消歧）把文件盘映射回平台全集，重建
本地下载/转写台账 inventory。

与 audit_disk 的分工：
  catalog   = 平台侧全量元数据基准（"应有什么"，脱敏、可入库）
  audit     = 文件盘 vs catalog 的对账报告（缺/重/游离/歧义）
  inventory = 每个已落盘文件的台账（id/oid/seq/file/实测时长/大小/转写路径）

用法：
  python rebuild_inventory.py \
    --catalog  library/00_manifest/catalog_<账号>.json \
    --video-root library/01_video/<行业>/<账号> \
    --transcript-root library/04_transcript/<行业>/<账号> \
    --domain stock \
    --out library/00_manifest/<账号>_inventory.json

严格校验门（任一不过则非零退出、不写台账）：
  - 每个磁盘文件必须唯一匹配 catalog 一条（无 orphan/ambiguous）
  - catalog 的 shorts/replays 必须被全部覆盖（无 missing）
  - 每个视频必须有 >50 字 transcript.md（视频与转写目录一一对应）
"""
import argparse, collections, importlib.util, json, os, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_audit():
    spec = importlib.util.spec_from_file_location("audit_disk", HERE / "audit_disk.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--video-root", required=True, help="其下有 short/ live/")
    ap.add_argument("--transcript-root", required=True, help="其下有 short/ live/<名>/transcript.md")
    ap.add_argument("--domain", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    au = load_audit()
    cat = json.load(open(args.catalog, encoding="utf-8"))
    for sec in ("shorts", "replays"):
        for e in cat.get(sec, []):
            e["_n"] = au.norm_title(e.get("title"))
            e["_tags"] = au.tag_words(e.get("title"))

    cache_path = os.path.join(args.video_root, ".duration_cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}

    repo_root = HERE.parents[2]  # platforms/wechat_channels/video-downloader -> 仓库根

    def section(entries, sub, classify):
        vdir = os.path.join(args.video_root, sub)
        tdir = os.path.join(args.transcript_root, sub)
        files = sorted(f for f in os.listdir(vdir) if f.endswith(".mp4")) if os.path.isdir(vdir) else []
        by_id = {e["id"]: e for e in entries}
        covered = collections.defaultdict(list)
        orphans, ambiguous, no_transcript, dur_mismatch = [], [], [], []
        recs = []
        for fname in files:
            path = os.path.join(vdir, fname)
            m = au.NAME_RE.match(fname)
            seq = int(m.group(2)) if m else -1
            dur = au.ffprobe_duration(path, cache)
            status, ids = au.match_file(fname, dur, entries, au.TOL[classify])
            if status == "multi":
                ambiguous.append({"file": fname, "candidate_ids": ids}); continue
            if status == "none":
                orphans.append(fname); continue
            e = by_id[ids[0]]
            stem = fname[:-4]
            tmd = os.path.join(tdir, stem, "transcript.md")
            tchars = len(open(tmd, encoding="utf-8", errors="ignore").read().strip()) if os.path.exists(tmd) else 0
            if tchars <= 50:
                no_transcript.append(fname)
            if dur is None or abs(dur - e["duration"]) > au.TOL[classify]:
                dur_mismatch.append({"file": fname, "disk": dur, "catalog": e["duration"]})
            covered[ids[0]].append(fname)
            recs.append({
                "id": e["id"], "oid": e.get("oid"), "seq": seq,
                "file": os.path.relpath(path, repo_root),
                "title": e["title"],
                "duration_s": round(dur) if dur is not None else None,
                "catalog_duration_s": e["duration"],
                "disk_size_mb": round(os.path.getsize(path) / 1048576, 1),
                "md5sum": e.get("md5"), "media_type": e.get("media_type"),
                "createtime": e.get("createtime"),
                "has_transcript": tchars > 50, "transcript_chars": tchars,
                "transcript_path": os.path.relpath(tmd, repo_root) if tchars > 50 else None,
            })
        missing = [e["id"] for e in entries if e["id"] not in covered]
        dup = {cid: fs for cid, fs in covered.items() if len(fs) > 1}
        recs.sort(key=lambda r: r["seq"])
        return {"recs": recs, "disk_files": len(files), "missing": missing,
                "orphans": orphans, "ambiguous": ambiguous, "dup": dup,
                "no_transcript": no_transcript, "dur_mismatch": dur_mismatch}

    sh = section(cat.get("shorts", []), "short", "short")
    lv = section(cat.get("replays", []), "live", "live")

    ok = True
    for label, s, expect in (("short", sh, len(cat.get("shorts", []))), ("live", lv, len(cat.get("replays", [])))):
        problems = []
        if s["missing"]: problems.append(f"缺{len(s['missing'])}")
        if s["orphans"]: problems.append(f"游离{len(s['orphans'])}")
        if s["ambiguous"]: problems.append(f"歧义{len(s['ambiguous'])}")
        if s["dup"]: problems.append(f"重复{len(s['dup'])}")
        if s["no_transcript"]: problems.append(f"无转写{len(s['no_transcript'])}")
        if s["dur_mismatch"]: problems.append(f"时长不符{len(s['dur_mismatch'])}")
        if len(s["recs"]) != expect: problems.append(f"条数{len(s['recs'])}≠{expect}")
        status = "✓" if not problems else "✗ " + ",".join(problems)
        print(f"[{label}] 磁盘{s['disk_files']} 台账{len(s['recs'])} 期望{expect} {status}")
        if problems:
            ok = False
            for p in ("missing", "orphans", "no_transcript"):
                for x in s[p][:10]:
                    print("   ", p, x)
            for x in s["ambiguous"][:10]:
                print("    ambiguous", x)

    if not ok:
        print("\n校验门未通过，不写 inventory。", file=sys.stderr)
        sys.exit(1)

    inv = {
        "account": cat.get("account"), "platform": cat.get("platform"),
        "domain": args.domain,
        "catalog_generated_at": cat.get("generated_at"),
        "inventory_generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "id_strategy": "id = md5(md5sum)[:16]（与 parse_capture_log.py / captor handleMedia 一致）",
        "summary": {
            "shorts": len(sh["recs"]), "lives": len(lv["recs"]),
            "shorts_with_transcript": sum(1 for r in sh["recs"] if r["has_transcript"]),
            "lives_with_transcript": sum(1 for r in lv["recs"] if r["has_transcript"]),
            "shorts_disk_size_mb": round(sum(r["disk_size_mb"] for r in sh["recs"]), 1),
            "lives_disk_size_mb": round(sum(r["disk_size_mb"] for r in lv["recs"]), 1),
        },
        "shorts": sh["recs"], "lives": lv["recs"],
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(inv, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\nInventory 已写入: {args.out}")
    print("  ", json.dumps(inv["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
