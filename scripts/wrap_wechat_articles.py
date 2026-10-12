#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wrap_wechat_articles.py — 为顶底之王公众号文章批量补 ArticleNote frontmatter（P3）。

原则（与桥文档 docs/workflow/article-to-okf-bridge.md §1、试点 stock-beishijijin 对齐）：
  * 幂等：content.md 首行已是 `---`（已有 frontmatter）则跳过；重复跑不重复加。
  * 只在 content.md 文件头插入 frontmatter 块，正文一字不动。
    校验：写入后文件字节数 == frontmatter 块字节数 + 原字节数，且原字节后缀逐字节相等。
  * 按文章日期倒序分批，每批 <= 50 篇（278 篇 -> 6 批：50/50/50/50/50/28）。
  * 不修改 article.json / manifest.json；06_articles 整体 gitignore，结果留在本地权威源。

用法：
  python3 wrap_wechat_articles.py --batch 1     # 只跑第 1 批（日期倒序后 [0:50]）
  python3 wrap_wechat_articles.py --batch 2 .. 6
  python3 wrap_wechat_articles.py --all         # 跑全部未 wrap 的（已 wrap 自动跳过）
  python3 wrap_wechat_articles.py --verify      # 校验全量 278：frontmatter 可解析 + 字段齐
  python3 wrap_wechat_articles.py --batch 1 --dry-run   # 只打印计划，不写盘

退出码：0 = 本批全部成功；1 = 任一文件校验失败（失败即停，不硬凑数量）。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs

import yaml

# ---------------------------------------------------------------------------
# 路径常量（脚本位于 content-pipeline/scripts/，仓库根 = 上一级）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO_ROOT, "library", "06_articles", "stock", "顶底之王")
MANIFEST = os.path.join(BASE, "manifest.json")

BATCH_SIZE = 50
TZ8 = timezone(timedelta(hours=8))
GENERATED_BY = "doubao/wrap_wechat_articles"

# content_type 关键词（标题命中即归类；howto 优先于 market_view，其余一律 market_view）
HOWTO_KW = ["如何", "方法", "教程", "技巧", "拆解"]
MARKET_VIEW_KW = ["收评", "复盘", "盘面", "缩量", "指数", "行情"]

# 从标题提取 1-2 个主题词的受控词表（命中即取，按标题出现顺序去重，最多 2 个）
THEME_WORDS = [
    "缩量", "放量", "地量", "北向", "北上", "资金面", "资金", "指数", "大盘", "板块",
    "牛市", "熊市", "慢牛", "支撑", "压力", "量能", "涨停", "跌停", "反弹", "回调",
    "突破", "变盘", "收评", "午评", "复盘", "盘面", "行情", "创业板", "科创板",
    "银行", "红利", "科技", "低估值", "龙头", "短线", "中线", "底部", "顶部",
    "阴线", "阳线", "破位", "低开", "高开", "轮动", "主线", "仓位", "满仓", "空仓",
    "震荡", "趋势", "高低切换",
]

REQUIRED_FIELDS = [
    "type", "title", "description", "tags", "domain", "content_type",
    "sources", "generated", "status", "published", "article_id",
]


# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(TZ8).replace(microsecond=0).isoformat()


def load_manifest():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


def sort_desc(manifest):
    """日期倒序；无日期(unknown-date)排最后。同日期按 id/index 倒序保证确定性。"""
    def key(x):
        date = x.get("date") or ""
        sid = x.get("id") or ("idx%d" % x.get("index", -1))
        return (date, sid)
    return sorted(manifest, key=key, reverse=True)


def get_mid(url):
    """从公众号 URL 提取 mid= 参数；无则返回 None。"""
    if not url:
        return None
    qs = parse_qs(urlparse(url).query)
    mid = qs.get("mid", [None])[0]
    return mid


def article_identity(x):
    """统一取 id（旧式 article_278）或 index（新式），用于日志与兜底。"""
    return x.get("id") or ("idx%d" % x.get("index", -1))


def extract_themes(title):
    picked = []
    for w in THEME_WORDS:
        if w in title and w not in picked:
            picked.append(w)
        if len(picked) >= 2:
            break
    if not picked:
        picked = ["A股"]
    return picked


def detect_content_type(title):
    for kw in HOWTO_KW:
        if kw in title:
            return "howto"
    for kw in MARKET_VIEW_KW:
        if kw in title:
            return "market_view"
    return "market_view"


def make_summary(x, content_md_path):
    """摘要优先用 manifest digest；否则取 content.md 首行截 ~90 字。"""
    dig = (x.get("digest") or "").strip()
    if dig:
        return dig
    try:
        with open(content_md_path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
    except Exception:
        first = ""
    first = re.sub(r"\s+", " ", first)
    if len(first) > 90:
        first = first[:90] + "…"
    return first or "（无摘要，待核）"


def build_frontmatter(x, generated_at):
    """构造 frontmatter dict。返回 (data_dict, article_id, published, warn_list)。"""
    title = x.get("title") or ""
    url = x.get("url") or ""
    date = x.get("date")  # 可能为 None

    # content.md 相对路径（仓库根 -> 采集层），用于 src-local-html.resource
    rel_content = os.path.join("library", "06_articles", "stock", "顶底之王",
                              x["local_path"], "content.md")

    # published：目录名日期 YYYY-MM-DD；unknown-date 如实标注
    published = date if date else "unknown-date"

    # article_id：wechat_<YYYYMMDD>_<mid>；无 mid 用 manifest id 兜底；无日期用 unknown
    mid = get_mid(url)
    if date:
        yyyymmdd = date.replace("-", "")
    else:
        yyyymmdd = "unknown"
    if mid:
        article_id = "wechat_%s_%s" % (yyyymmdd, mid)
    else:
        article_id = "wechat_%s_%s" % (yyyymmdd, article_identity(x))

    themes = extract_themes(title)
    ctype = detect_content_type(title)
    summary = make_summary(x, os.path.join(BASE, x["local_path"], "content.md"))

    data = {
        "type": "ArticleNote",
        "title": title,
        "description": "机器生成待核：%s" % summary,
        "tags": ["顶底之王", "stock", "公众号"] + themes,
        "domain": "stock",
        "content_type": ctype,
        "sources": [
            {
                "id": "src-wechat",
                "kind": "wechat_article",
                "resource": url,
                "title": title,
            },
            {
                "id": "src-local-html",
                "kind": "local_html",
                "resource": rel_content,
                "title": "本地落盘正文（content.md，采集层原文，未改）",
            },
        ],
        "generated": {"by": GENERATED_BY, "at": generated_at},
        "status": "draft",
        "published": published,
        "article_id": article_id,
    }

    warns = []
    if not date:
        warns.append("no-date(published=unknown-date,article_id=wechat_unknown_*)")
    if not mid:
        warns.append("no-mid(fallback-to-manifest-id)")
    return data, article_id, published, warns


def render_block(data):
    """把 dict 渲染成 frontmatter 字节块（含首尾 --- 与末尾换行）。"""
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                          default_flow_style=False, width=1000)
    if not body.endswith("\n"):
        body += "\n"
    block = "---\n" + body + "---\n"
    return block.encode("utf-8")


def already_wrapped(content_bytes):
    return content_bytes.startswith(b"---\n")


def wrap_one(x, generated_at, dry_run=False):
    """wrap 单篇。返回 (status, info_dict)。status in {wrapped, skipped, error}。"""
    rel = x["local_path"]
    cm = os.path.join(BASE, rel, "content.md")
    if not os.path.exists(cm):
        return "error", {"id": article_identity(x), "err": "content.md missing: %s" % rel}

    with open(cm, "rb") as f:
        orig = f.read()

    if already_wrapped(orig):
        return "skipped", {"id": article_identity(x), "path": rel}

    data, aid, published, warns = build_frontmatter(x, generated_at)
    block = render_block(data)

    # 渲染后自检：yaml 可解析 + 字段齐
    try:
        parsed = yaml.safe_load(block.split(b"---\n", 2)[1].decode("utf-8"))
    except Exception as e:
        return "error", {"id": article_identity(x), "err": "yaml parse: %s" % e}
    missing = [k for k in REQUIRED_FIELDS if k not in parsed]
    if missing:
        return "error", {"id": article_identity(x), "err": "missing fields: %s" % missing}

    new_bytes = block + orig
    if dry_run:
        return "wrapped", {"id": article_identity(x), "article_id": aid,
                           "published": published, "ctype": data["content_type"],
                           "themes": data["tags"][3:], "orig_bytes": len(orig),
                           "block_bytes": len(block), "warns": warns}

    # 写盘前再断言一次拼接关系（防手抖改错）
    assert new_bytes[:len(block)] == block
    assert new_bytes[len(block):] == orig
    with open(cm, "wb") as f:
        f.write(new_bytes)

    # 写后读回校验：字节数 == orig + block，正文后缀未动
    with open(cm, "rb") as f:
        after = f.read()
    if len(after) != len(orig) + len(block):
        return "error", {"id": article_identity(x),
                         "err": "byte mismatch after write: %d != %d+%d"
                         % (len(after), len(orig), len(block))}
    if after[len(block):] != orig:
        return "error", {"id": article_identity(x), "err": "body bytes changed"}

    return "wrapped", {"id": article_identity(x), "article_id": aid,
                        "published": published, "ctype": data["content_type"],
                        "themes": data["tags"][3:], "orig_bytes": len(orig),
                        "block_bytes": len(block), "warns": warns, "path": rel}


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def cmd_batch(batch_no, dry_run):
    manifest = sort_desc(load_manifest())
    batches = list(chunks(manifest, BATCH_SIZE))
    if batch_no < 1 or batch_no > len(batches):
        print("ERROR: batch %d out of range (1..%d)" % (batch_no, len(batches)))
        return 1
    target = batches[batch_no - 1]
    generated_at = now_iso()

    wrapped = skipped = errs = 0
    err_list = []
    warn_list = []
    print("=== batch %d/%d  size=%d  generated_at=%s ==="
          % (batch_no, len(batches), len(target), generated_at))
    for x in target:
        st, info = wrap_one(x, generated_at, dry_run=dry_run)
        if st == "wrapped":
            wrapped += 1
            if info.get("warns"):
                warn_list.append((info["id"], info["warns"]))
        elif st == "skipped":
            skipped += 1
        else:
            errs += 1
            err_list.append(info)
            print("  ERROR %s: %s" % (info["id"], info["err"]))
            break  # 失败即停

    print("--- batch %d result: wrapped=%d skipped=%d errors=%d ---"
          % (batch_no, wrapped, skipped, errs))
    if warn_list:
        print("  warns (%d):" % len(warn_list))
        for i, w in warn_list:
            print("    %s: %s" % (i, "; ".join(w)))
    if errs:
        print("  FAILED batch %d" % batch_no)
        return 1
    return 0


def cmd_all(dry_run):
    manifest = sort_desc(load_manifest())
    generated_at = now_iso()
    wrapped = skipped = errs = 0
    for x in manifest:
        st, info = wrap_one(x, generated_at, dry_run=dry_run)
        if st == "wrapped":
            wrapped += 1
        elif st == "skipped":
            skipped += 1
        else:
            errs += 1
            print("ERROR %s: %s" % (info["id"], info["err"]))
            break
    print("ALL: wrapped=%d skipped=%d errors=%d (total manifest=%d)"
          % (wrapped, skipped, errs, len(manifest)))
    return 0 if errs == 0 else 1


def cmd_verify():
    """全量校验：278 篇都已 wrap、frontmatter 可解析、字段齐、sources 两条。"""
    manifest = load_manifest()
    ok = 0
    errs = []
    for x in manifest:
        cm = os.path.join(BASE, x["local_path"], "content.md")
        if not os.path.exists(cm):
            errs.append((article_identity(x), "content.md missing"))
            continue
        with open(cm, "rb") as f:
            raw = f.read()
        if not raw.startswith(b"---\n"):
            errs.append((article_identity(x), "no frontmatter"))
            continue
        # 截取第二个 --- 之间的块
        try:
            text = raw.decode("utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            if not m:
                errs.append((article_identity(x), "frontmatter block not closed"))
                continue
            data = yaml.safe_load(m.group(1))
        except Exception as e:
            errs.append((article_identity(x), "yaml parse: %s" % e))
            continue
        missing = [k for k in REQUIRED_FIELDS if k not in data]
        if missing:
            errs.append((article_identity(x), "missing: %s" % missing))
            continue
        src_ids = [s.get("id") for s in data["sources"]]
        if src_ids != ["src-wechat", "src-local-html"]:
            errs.append((article_identity(x), "sources ids != [src-wechat, src-local-html]: %s" % src_ids))
            continue
        if data["type"] != "ArticleNote" or data["status"] != "draft" or data["domain"] != "stock":
            errs.append((article_identity(x), "type/status/domain off"))
            continue
        ok += 1
    print("VERIFY: ok=%d / total=%d  errors=%d" % (ok, len(manifest), len(errs)))
    for e in errs[:30]:
        print("  ERR %s: %s" % (e[0], e[1]))
    return 0 if not errs else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, help="只跑指定批次（1-based）")
    ap.add_argument("--all", action="store_true", help="跑全部未 wrap 的")
    ap.add_argument("--verify", action="store_true", help="全量校验已 wrap 的 frontmatter")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划不写盘")
    args = ap.parse_args()

    if args.verify:
        return cmd_verify()
    if args.batch is not None:
        return cmd_batch(args.batch, args.dry_run)
    if args.all:
        return cmd_all(args.dry_run)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
