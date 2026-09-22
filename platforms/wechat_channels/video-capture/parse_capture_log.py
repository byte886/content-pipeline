#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_capture_log.py — 重组 video-capture 注入 JS 上报到 `_api.log` 的全量清单。

方案 B（Pinia action 驱动）的离线落地器：captor 把注入 JS 的 fetch 上报文本记录在
`<output>.json` 同名的 `_api.log` 里。本脚本把其中的分块 payload 重组回 Pinia store
快照（cardObjects 短视频 / liveCardObjects 直播回放），并产出两类文件：

1. 脱敏 catalog（平台侧全量元数据基准，权威落位 library/00_manifest/catalog_<账号>.json，可入库）：
   只含 id/oid/标题/时长/size/md5/清晰度规格/互动数据等元数据，**不含任何 token/decodeKey**。
   它回答"平台上全集是什么"；与下载台账 inventory（"本地下了哪些文件"）按 16hex id 关联。
2. 含票据 signed 清单（默认写 workspace/signed/，整目录被 .gitignore 忽略，禁止入 public 仓）：
   仅当 cardObject 自带 urlToken/decodeKey 时生成，字段对齐 batch_download_v4.py（数组）
   与 incremental_sync.py（shorts/replays 字典），可直接喂下载器。

上报协议（与 replay_list_hook.go 保持一致）：
  日志记录: [yyyy-mm-dd HH:MM:SS] POST wxapp.tc.qq.com/res-downloader/wechat?type=3
            Headers: ...
            Body: {"type":"page_html","url":...,"html":"<TAG payload>"}
  payload 整块: <TAG>__<descriptor>__0__<json>
  payload 分块: <TAG>__<descriptor>__<rid>__<i>__<n>__<chunk>
  FEED 的 descriptor = "<path>__len=<N>"，其余 tag 的 descriptor = "<path>"。

稳定主键与 captor.go handleMedia 完全一致：
  id = md5(md5sum)[:16]；无 md5sum 时退化为 md5(rawURL)[:16]。
  可播放直链：短视频 = media.url + media.urlToken（urlToken 形如 "&token=..."，直接拼接）；
  回放 = url 本身已内嵌 "&token=..."（urlToken 留空）。统一以最终 URL 是否含 "token=" 判定已签名。

用法（在仓库根目录执行）:
  python3 platforms/wechat_channels/video-capture/parse_capture_log.py <capture_api.log> \
      --account 交易的游戏 \
      --catalog-out "library/00_manifest/catalog_交易的游戏.json" \
      --signed-dir workspace/signed
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------- 日志/payload 解析

REC_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] ", re.M)
HDR_RE = re.compile(r"__(?:0|(\d{6,})__(\d+)__(\d+))__")
TAG_RE = re.compile(r"(RLIST_[A-Z]+|SP_[A-Z]+)__")
LEN_SUFFIX_RE = re.compile(r"__len=\d+$")


def iter_bodies(data: str):
    """切分日志记录，yield 每条 type=3 上报 Body 里的明文 html payload。"""
    for rec in REC_RE.split(data):
        if "res-downloader/wechat?type=3" not in rec or "Body:" not in rec:
            continue
        body = rec.split("Body:", 1)[1].strip()
        obj = None
        try:
            obj = json.loads(body)
        except Exception:
            try:
                obj = json.loads(body[: body.rfind("}") + 1])
            except Exception:
                obj = None
        if isinstance(obj, dict) and obj.get("html"):
            yield obj["html"]


def parse_payload(html: str):
    """返回 (tag, descriptor, rid, i, n, chunk)，无法解析返回 None。"""
    m = TAG_RE.match(html)
    if not m:
        return None
    tag = m.group(1)
    rest = html[m.end():]
    hm = HDR_RE.search(rest)
    if not hm:
        return None
    descriptor = rest[: hm.start()]
    chunk = rest[hm.end():]
    if hm.group(1) is None:  # 整块 __0__
        return tag, descriptor, "0", 0, 1, chunk
    return tag, descriptor, hm.group(1), int(hm.group(2)), int(hm.group(3)), chunk


def assemble(data: str):
    """重组所有收齐的 payload，返回 {tag: [(descriptor, value), ...]}。"""
    slots = collections.defaultdict(dict)
    for html in iter_bodies(data):
        p = parse_payload(html)
        if not p:
            continue
        tag, desc, rid, i, n, chunk = p
        g = slots[(tag, desc, rid)]
        g["n"] = n
        g[i] = chunk
    out = collections.defaultdict(list)
    for (tag, _desc, _rid), g in slots.items():
        try:
            n = int(g.get("n", 1))
        except Exception:
            n = 1
        if not all(k in g for k in range(n)):
            continue  # 分块未收齐，跳过（避免半截 JSON）
        raw = "".join(g[k] for k in range(n))
        try:
            out[tag].append((_desc, json.loads(raw)))
        except Exception:
            continue
    return out


def best_feed_snapshot(assembled, suffix: str):
    """取 RLIST_FEED 中指定 path（cardObjects/liveCardObjects）元素最多的快照。"""
    best = None
    for desc, val in assembled.get("RLIST_FEED", []):
        path = LEN_SUFFIX_RE.sub("", desc)
        if not path.endswith(suffix) or not isinstance(val, list):
            continue
        m = re.search(r"len=(\d+)$", desc)
        ln = int(m.group(1)) if m else len(val)
        if best is None or ln > best[0]:
            best = (ln, val)
    return best[1] if best else []


def drive_progress(assembled):
    """取 RLIST_DRIVE 最后一条进度（all-done 含 short/live 计数）。"""
    prog = None
    for _desc, val in assembled.get("RLIST_DRIVE", []):
        if isinstance(val, dict):
            prog = val
    return prog or {}


# ---------------------------------------------------------------- cardObject 映射

def md5_hex(s: str) -> str:
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()


def _specs(media_spec, slim_specs):
    """归一化清晰度规格，返回 (formats:[fileFormat...], best_format, raw)。"""
    src = media_spec if isinstance(media_spec, list) else (slim_specs if isinstance(slim_specs, list) else [])
    formats, best, best_br = [], "", -1
    for it in src:
        if not isinstance(it, dict):
            continue
        ff = it.get("fileFormat") or it.get("xwt") or it.get("format")
        if ff:
            formats.append(str(ff))
        br = it.get("videoBitrate") or it.get("bitrate") or it.get("bitRate") or 0
        try:
            br = float(br)
        except Exception:
            br = 0
        if ff and br > best_br:
            best_br, best = br, str(ff)
    return formats, best, src


def extract(c: dict):
    """把一个 cardObject（slim 扁平 或 完整 objectDesc 嵌套）映射为统一字典。"""
    od = c.get("objectDesc")
    if isinstance(od, str):
        try:
            od = json.loads(od)
        except Exception:
            od = None
    media = od.get("media", []) if isinstance(od, dict) else None
    media = media[0] if isinstance(media, list) and media and isinstance(media[0], dict) else None

    if media is not None:  # 完整嵌套形态
        raw_url = media.get("url", "") or ""
        url_token = media.get("urlToken", "") or ""
        decode_key = str(media.get("decodeKey", "") or "")
        md5 = (media.get("md5sum", "") or "").lower()
        size = media.get("cdnFileSize") or media.get("fileSize") or 0
        dur = media.get("videoPlayLen") or 0
        width, height = media.get("width"), media.get("height")
        mtype = media.get("mediaType")
        cover = media.get("coverUrl") or media.get("thumbUrl") or ""
        title = (od.get("description") or c.get("desc") or "").strip()
        formats, best_fmt, raw_spec = _specs(media.get("spec"), None)
        hls = media.get("hlsSpec")
    else:                  # slim 扁平形态（hook 主动瘦身上报）
        raw_url = c.get("url", "") or ""
        url_token = c.get("urlToken", "") or ""
        decode_key = str(c.get("decodeKey", "") or c.get("decode_key", "") or "")
        md5 = (c.get("md5") or c.get("md5sum") or "").lower()
        size = c.get("cdnFileSize") or c.get("fileSize") or c.get("size") or 0
        dur = c.get("videoPlayLen") or 0
        if not dur and c.get("durMs"):  # 兜底毫秒
            try:
                dur = int(c["durMs"]) // 1000
            except Exception:
                dur = 0
        width, height = c.get("w") or c.get("width"), c.get("h") or c.get("height")
        mtype = c.get("mediaType")
        cover = c.get("cover") or c.get("coverUrl") or ""
        title = (c.get("desc") or "").strip()
        formats, best_fmt, raw_spec = _specs(None, c.get("specs"))
        hls = c.get("hlsSpec")

    try:
        size = int(size)
    except Exception:
        size = 0
    try:
        dur = int(dur)
    except Exception:
        dur = 0
    uid = md5_hex(md5)[:16] if md5 else md5_hex(raw_url)[:16]
    # 可播放直链两种形态：
    #   短视频 = 无 token 的 url + 独立 urlToken（urlToken 形如 "&token=…"）
    #   回放   = url 本身已内嵌 "?encfilekey=…&token=…"，urlToken 字段留空
    if url_token and "token=" not in raw_url:
        signed_url = raw_url + url_token
    else:
        signed_url = raw_url
    has_token = "token=" in signed_url
    return {
        "id": uid,
        "oid": str(c.get("oid") or c.get("objectId") or c.get("id") or ""),
        "nid": str(c.get("nid") or c.get("objectNonceId") or ""),
        "title": title,
        "duration": dur,
        "size": size,
        "md5": md5,
        "media_type": mtype,
        "width": width,
        "height": height,
        "cover": cover,
        "formats": formats,
        "best_format": best_fmt,
        "createtime": c.get("ct") or c.get("createtime") or 0,
        "stats": {k: c.get(k) for k in ("like", "fav", "fwd", "cmt", "read",
                                        "likeCount", "favCount", "forwardCount",
                                        "commentCount", "readCount") if k in c},
        "ip": c.get("ip") or (c.get("ipRegionInfo") or {}),
        # 票据相关（仅 signed 产物使用；catalog 会剥离）
        "_raw_url": raw_url,
        "_signed_url": signed_url,
        "_decode_key": decode_key,
        "_has_url_token": has_token,
        "_hls": hls,
    }


def split_sections(cards):
    """按 mediaType 拆 短视频(4)/图文(2)/其它，按 oid+md5 去重。"""
    shorts, images, others = [], [], []
    seen = set()
    for c in cards:
        if not isinstance(c, dict):
            continue
        m = extract(c)
        key = m["oid"] or m["md5"] or m["id"]
        if key in seen:
            continue
        seen.add(key)
        mt = str(m["media_type"])
        if mt == "4":
            shorts.append(m)
        elif mt == "2":
            images.append(m)
        else:
            others.append(m)
    return shorts, images, others


# ---------------------------------------------------------------- 输出

PUBLIC_FIELDS = ("id", "oid", "nid", "title", "duration", "size", "md5", "media_type",
                 "width", "height", "formats", "best_format", "createtime",
                 "stats", "ip")


def public_view(m: dict, classify: str):
    # 封面 URL 带 encfilekey+临时 token 签名，禁止入 public 仓，降级为布尔标记
    d = {k: m[k] for k in PUBLIC_FIELDS}
    d["has_cover"] = bool(m["cover"])
    d["has_signed"] = m["_has_url_token"]
    d["classify"] = classify
    return d


def signed_view(m: dict, classify: str, account: str):
    return {
        "id": m["id"],
        "url": m["_signed_url"],
        "decode_key": m["_decode_key"],
        "description": m["title"],
        "short_title": m["title"][:60],
        "size": m["size"],
        "md5": m["md5"],
        "duration": m["duration"],
        "width": m["width"],
        "height": m["height"],
        "classify": classify,
        "suffix": ".mp4",
        "account": account,
        "best_format": m["best_format"],
        "wx_file_formats": "#".join(m["formats"]),
        "captured_via": "action-pinia",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="captor 落盘的 *_api.log 路径")
    ap.add_argument("--account", default="交易的游戏", help="视频号账号名（台账归属）")
    ap.add_argument("--catalog-out", default=None, help="脱敏 catalog 输出 JSON（可入库）")
    ap.add_argument("--signed-dir", default=None, help="含票据清单输出目录（应在 .gitignore 内，如 workspace/signed）")
    args = ap.parse_args()

    with open(args.log, encoding="utf-8", errors="replace") as f:
        data = f.read()
    assembled = assemble(data)
    cards = best_feed_snapshot(assembled, "cardObjects")
    lives = best_feed_snapshot(assembled, "liveCardObjects")
    prog = drive_progress(assembled)

    shorts, images, _other = split_sections(cards)
    replays, live_images, _ = split_sections(lives)
    images += live_images

    sw_url = sum(1 for m in shorts if m["_has_url_token"])
    sw_key = sum(1 for m in shorts if m["_decode_key"])
    lv_url = sum(1 for m in replays if m["_has_url_token"])

    catalog = {
        "account": args.account,
        "platform": "wechat_channels",
        "source_log": os.path.basename(args.log),
        "generated_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "drive": {k: prog.get(k) for k in ("stage", "short", "live")},
        "counts": {"shorts": len(shorts), "replays": len(replays), "image_posts": len(images)},
        "signed_coverage": {
            "shorts_with_url_token": sw_url,
            "shorts_with_decode_key": sw_key,
            "replays_with_url_token": lv_url,
        },
        "shorts": [public_view(m, "short") for m in shorts],
        "replays": [public_view(m, "live") for m in replays],
        "image_posts": [public_view(m, "image") for m in images],
    }

    if args.catalog_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.catalog_out)), exist_ok=True)
        with open(args.catalog_out, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"[catalog] 脱敏清单（可入库）: {args.catalog_out}")

    print(json.dumps({
        "drive": catalog["drive"],
        "counts": catalog["counts"],
        "signed_coverage": catalog["signed_coverage"],
    }, ensure_ascii=False, indent=2))

    # 含票据清单：仅当确实拿到 urlToken 时才写，避免产生空/误导文件
    have_signed = sw_url > 0 or lv_url > 0
    if args.signed_dir and have_signed:
        os.makedirs(args.signed_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(args.log))[0]
        s_shorts = [signed_view(m, "short", args.account) for m in shorts if m["_has_url_token"]]
        s_lives = [signed_view(m, "live", args.account) for m in replays if m["_has_url_token"]]
        manifest = {"account": args.account, "generated_at": catalog["generated_at"],
                    "shorts": s_shorts, "replays": s_lives}
        mp = os.path.join(args.signed_dir, f"{stem}_manifest_signed.json")
        sp = os.path.join(args.signed_dir, f"{stem}_signed_shorts.json")
        lp = os.path.join(args.signed_dir, f"{stem}_signed_lives.json")
        for path, obj in ((mp, manifest), (sp, s_shorts), (lp, s_lives)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        print(f"[signed] 含票据清单（勿入库）: {mp}\n         {sp} ({len(s_shorts)})\n         {lp} ({len(s_lives)})")
    elif args.signed_dir:
        print("[signed] 本次快照无 urlToken（hook 未取或未换签），未生成含票据清单。")


if __name__ == "__main__":
    main()
