#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_disk.py — 文件盘视频 vs 平台全量 catalog 的严格对账（去重/缺口/游离）。

背景：mp4 文件 MD5 与 catalog 的高清 md5sum 跨清晰度对不上（命中率近 0），不能用作对账键。
本工具用 **ffprobe 实际时长 + 归一化标题（+ hashtag 消歧）** 把磁盘文件映射回 catalog 条目
（id = md5(md5sum)[:16]，由 parse_capture_log.py 生成），输出：
  - missing：catalog 有、磁盘没有的条目（真实下载缺口）
  - duplicate_groups：同一 catalog 条目对应多个磁盘文件（重复下载，给出保留/删除建议，不自动删）
  - orphan：磁盘有、但不匹配任何 catalog 条目的文件（游离，可能下错/标题异常）
  - ambiguous：一个文件同时匹配多条目（靠 hashtag/时长仍无法消歧），需人工看一眼

同名多场次（如三次"再次缩量见底"、六次"回调就是进场机会"）靠时长精确区分；
同标题同时长但 hashtag 不同的两条视频（如两条"A股支撑已到"）靠文件名/标题标签词重合消歧。

用法:
  python3 audit_disk.py --catalog catalog_jiaoyi.json \
      --video-root library/01_video/stock/交易的游戏 \
      --out library/00_manifest/audit_交易的游戏.json
时长缓存落在 <video-root>/.duration_cache.json，重复运行/增量对账时秒级返回。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import collections

FFPROBE = os.environ.get("FFPROBE", "ffprobe")
TOL = {"short": 2, "live": 3}          # 时长容差（秒）
NAME_RE = re.compile(r"^(short|live)_(\d+)_(.+)\.mp4$")


def norm_title(t: str) -> str:
    t = (t or "").split("\n")[0]
    t = re.sub(r"#\S+", "", t)
    return re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", t)[:10]


def tag_words(t: str) -> set:
    """标题里 #标签 的词 + 全文非中文英文数字片段，用于同名同时长消歧。"""
    tags = re.findall(r"#([^#\s]+)", t or "")
    words = set()
    for tg in tags:
        words.update(x for x in re.split(r"[\s,，、_/]+", tg) if x)
    return words


def fname_words(fname: str) -> set:
    m = NAME_RE.match(fname)
    body = m.group(3) if m else fname
    return set(x for x in re.split(r"[_\s,，、!！?？.。]+", body) if len(x) >= 2)


def ffprobe_duration(path: str, cache: dict) -> float | None:
    st = os.stat(path)
    key = f"{path}:{st.st_size}:{int(st.st_mtime)}"
    if key in cache:
        return cache[key]
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path],
                           capture_output=True, text=True, timeout=30)
        v = float(r.stdout.strip())
    except Exception:
        v = None
    cache[key] = v
    return v


def match_file(fname: str, dur, entries, tol):
    """返回 (status, [entry ids])。status=ok/multi/none。"""
    m = NAME_RE.match(fname)
    body = m.group(3) if m else fname.replace(".mp4", "")
    fn = norm_title(body)          # 必须先剥 short_NNN_/live_NNN_ 前缀，否则 [:10] 截到的是前缀
    fw = fname_words(fname)
    cands = []
    for e in entries:
        en = e["_n"]
        if not en or not (en in fn or fn in en):
            continue
        if dur is None or abs(dur - e["duration"]) > tol:
            continue
        cands.append(e)
    if len(cands) == 1:
        return "ok", [cands[0]["id"]]
    if len(cands) == 0:
        return "none", []
    # 多候选：标签词重合优先，其次时长最接近
    def score(e):
        overlap = len(fw & e["_tags"])
        dtie = -abs(dur - e["duration"])
        return (overlap, dtie)
    cands.sort(key=score, reverse=True)
    best, second = score(cands[0]), score(cands[1])
    if best[0] > second[0] or (best[0] == second[0] and best[1] > second[1]):
        return "ok", [cands[0]["id"]]
    return "multi", [c["id"] for c in cands]


def audit_section(entries, video_dir, classify, cache):
    files = sorted(f for f in os.listdir(video_dir) if f.endswith(".mp4")) if os.path.isdir(video_dir) else []
    entry_files = collections.defaultdict(list)
    orphan, ambiguous = [], []
    for fname in files:
        path = os.path.join(video_dir, fname)
        m = NAME_RE.match(fname)
        seq = int(m.group(2)) if m else -1
        dur = ffprobe_duration(path, cache)
        size_mb = round(os.path.getsize(path) / 1048576, 1)
        status, ids = match_file(fname, dur, entries, TOL[classify])
        rec = {"seq": seq, "file": fname, "duration": round(dur) if dur is not None else None,
               "size_mb": size_mb}
        if status == "ok":
            entry_files[ids[0]].append(rec)
        elif status == "multi":
            ambiguous.append({**rec, "candidate_ids": ids})
        else:
            orphan.append(rec)
    covered = set(entry_files)
    missing = [{"id": e["id"], "oid": e.get("oid"), "title": e["title"],
                "duration": e["duration"], "size": e.get("size")}
               for e in entries if e["id"] not in covered]
    dup_groups = []
    for cid, recs in entry_files.items():
        if len(recs) > 1:
            # 知识型默认 min 清晰度：建议保留最小可用文件（可正常播放前提下）；这里只给建议，不删
            keep = min(recs, key=lambda r: r["size_mb"])
            drop = [r for r in recs if r is not keep]
            e = next(x for x in entries if x["id"] == cid)
            dup_groups.append({"id": cid, "title": e["title"], "duration": e["duration"],
                               "keep": keep, "drop": drop,
                               "saving_mb": round(sum(r["size_mb"] for r in drop), 1)})
    return {
        "catalog_total": len(entries), "disk_files": len(files),
        "covered": len(covered), "missing_count": len(missing), "missing": missing,
        "duplicate_groups_count": len(dup_groups),
        "duplicate_files_to_remove": sum(len(g["drop"]) for g in dup_groups),
        "duplicate_groups": dup_groups,
        "orphan_count": len(orphan), "orphan": orphan,
        "ambiguous_count": len(ambiguous), "ambiguous": ambiguous,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", required=True, help="parse_capture_log.py 产出的脱敏 catalog JSON")
    ap.add_argument("--video-root", required=True, help="账号视频根目录（其下有 short/ live/）")
    ap.add_argument("--out", required=True, help="对账报告输出 JSON")
    args = ap.parse_args()

    cat = json.load(open(args.catalog, encoding="utf-8"))
    for sec in ("shorts", "replays"):
        for e in cat.get(sec, []):
            e["_n"] = norm_title(e.get("title"))
            e["_tags"] = tag_words(e.get("title"))

    cache_path = os.path.join(args.video_root, ".duration_cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}

    report = {
        "account": cat.get("account"), "platform": cat.get("platform"),
        "video_root": args.video_root,
        "catalog_counts": cat.get("counts"),
        "short": audit_section(cat.get("shorts", []), os.path.join(args.video_root, "short"), "short", cache),
        "live": audit_section(cat.get("replays", []), os.path.join(args.video_root, "live"), "live", cache),
    }
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(report, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    for key, label in (("short", "短视频"), ("live", "直播回放")):
        r = report[key]
        print(f"[{label}] 全集{r['catalog_total']} 磁盘{r['disk_files']} 覆盖{r['covered']} "
              f"缺{r['missing_count']} 重复组{r['duplicate_groups_count']}(待删{r['duplicate_files_to_remove']}) "
              f"游离{r['orphan_count']} 歧义{r['ambiguous_count']}")
        for m in r["missing"]:
            print(f"    缺 {m['id']} {m['duration']}s {m['title'][:30]}")
        for a in r["ambiguous"]:
            print(f"    歧义 {a['file']} -> {a['candidate_ids']}")
    print(f"报告: {args.out}（时长缓存: {cache_path}）")


if __name__ == "__main__":
    main()
