#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fused_into_reconcile.py — fused_into 双向指针完整性复核（幂等、只读）

复核范围（K4 质检加固·任务一）：
  采集层：
    - library/06_articles/jewelry/宝石学家老许/articles/*/meta.json      (字段 fused_into)
    - library/06_articles/stock/顶底之王/articles/*/article.json       (字段 fused_into)
  知识层（反向引用对账）：
    - 老许 topics 页 sources 里必须出现 opus-<meta.id>
    - 顶底之王 articles 页必须能反指回采集目录（src-local-html resource / article_id）

检查项：
  FWD_MISSING   采集层 fused_into 指向的知识层文件不存在（悬空指针）
  FWD_DUP       多个采集源指向同一个知识层文件（重复指针；topics 聚合页除外，记为正常）
  BACK_MISSING 知识层文件存在，但反指不到该采集源（缺反向背书）
  ORPHAN        知识层 topics/articles 页没有任何采集层 forward 指针指向它
  DANGLING_REF  知识层文件存在但内容无法解析出 sources（解析异常，单独提示）

退出码：恒为 0（只读对账，不抛错）；结论打印到 stdout。
用法：
  python3 scripts/fused_into_reconcile.py            # 人类可读报告
  python3 scripts/fused_into_reconcile.py --json     # JSON 报告
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLL = REPO / "library" / "06_articles"

LAOXU_DIR = COLL / "jewelry" / "宝石学家老许" / "articles"
DINGDI_DIR = COLL / "stock" / "顶底之王" / "articles"

KNOW = REPO / "library" / "05_knowledge"
JEWELRY_TOPICS = KNOW / "jewelry" / "concepts" / "topics"
STOCK_ARTICLES = KNOW / "stock" / "concepts" / "articles"

# frontmatter sources[].id 提取（兼容两种写法）：
#   块式:  - id: src-bili
#   流式:  { id: "opus-123...", resource: ... }
# 只取紧跟在行首/'- '/'{ '之后的 id:，避开 book_id:/article_id: 等顶层键。
SRC_ID_RE = re.compile(r"(?:^|[-{]\s+)id:\s*[\"']?([^\"'\n,}]+?)[\"']?\s*[,}\n]", re.M)
FM_SPLIT_RE = re.compile(r"^---\s*$")


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def frontmatter_text(md: str) -> str:
    """返回 --- 之间的 frontmatter 文本；无则空串。"""
    lines = md.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    out = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            return "\n".join(out)
        out.append(ln)
    return ""


def source_ids(md_path: Path):
    """提取知识层 md frontmatter sources[].id 列表。"""
    if not md_path.exists():
        return None
    fm = frontmatter_text(md_path.read_text(encoding="utf-8"))
    if fm == "":
        return []
    return [s.strip() for s in SRC_ID_RE.findall(fm)]


def resource_lines(md_path: Path):
    """提取 frontmatter 里所有 resource: 路径（用于反指采集目录）。"""
    fm = frontmatter_text(md_path.read_text(encoding="utf-8")) if md_path.exists() else ""
    return re.findall(r"resource:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", fm, re.M)


def fused_target_to_path(t: str) -> Path:
    """fused_into 值形如 '05_knowledge/jewelry/...' → 仓库内绝对路径。"""
    t = t.strip().lstrip("/")
    if t.startswith("library/"):
        return REPO / t
    return REPO / "library" / t


def main():
    report = {
        "forward_total": 0,
        "forward_by_source": {},
        "fwd_missing": [],        # 悬空
        "fwd_dup": {},            # target -> [采集源...]
        "back_missing": [],       # 缺反向背书
        "orphan_topics": [],
        "orphan_articles": [],
        "parse_warn": [],
    }

    # ---- 采集层 forward 指针采集 ----
    fwd = []  # (collector_kind, collection_file, collection_dir, fused_into_value, target_path)

    # 老许 meta.json
    laoxu_count = 0
    for mj in sorted(LAOXU_DIR.glob("*/meta.json")):
        data = read_json(mj)
        if not data:
            report["parse_warn"].append(str(mj.relative_to(REPO)) + " (meta.json 解析失败)")
            continue
        fi = data.get("fused_into")
        if not fi:
            continue
        laoxu_count += 1
        cid = str(data.get("id", ""))
        fwd.append(("laoxu", mj, mj.parent, fi, fused_target_to_path(fi), {"meta_id": cid}))
    report["forward_by_source"]["laoxu_meta.json"] = laoxu_count

    # 顶底之王 article.json
    dingdi_count = 0
    for aj in sorted(DINGDI_DIR.glob("*/article.json")):
        data = read_json(aj)
        if not data:
            report["parse_warn"].append(str(aj.relative_to(REPO)) + " (article.json 解析失败)")
            continue
        fi = data.get("fused_into")
        if not fi:
            continue
        dingdi_count += 1
        fwd.append(("dingdi", aj, aj.parent, fi, fused_target_to_path(fi), {}))
    report["forward_by_source"]["dingdi_article.json"] = dingdi_count
    report["forward_total"] = len(fwd)

    # ---- forward 悬空 + 重复 ----
    target_to_sources = {}
    for kind, cfile, cdir, fival, tpath, extra in fwd:
        if not tpath.exists():
            report["fwd_missing"].append({
                "collector": kind,
                "collection_file": str(cfile.relative_to(REPO)),
                "fused_into": fival,
                "resolved_target": str(tpath.relative_to(REPO)),
            })
            continue
        key = str(tpath)
        target_to_sources.setdefault(key, []).append((kind, cfile, cdir, extra))

    for key, lst in target_to_sources.items():
        if len(lst) > 1:
            # topics 聚合页本来就多对一；articles 页一对一
            report["fwd_dup"][str(Path(key).relative_to(REPO))] = {
                "count": len(lst),
                "note": "聚合页(topics)多对一为正常；articles 页多对一为异常",
                "collectors": [str(c.relative_to(REPO)) for _, c, _, _ in lst],
            }

    # ---- 反向背书 ----
    for kind, cfile, cdir, fival, tpath, extra in fwd:
        if not tpath.exists():
            continue
        if kind == "laoxu":
            # topics 页 sources 需出现 opus-<meta_id>
            ids = source_ids(tpath)
            if ids is None:
                report["parse_warn"].append(str(tpath.relative_to(REPO)) + " (sources 解析失败)")
                continue
            want = "opus-" + extra["meta_id"]
            if want not in ids:
                report["back_missing"].append({
                    "collector": "laoxu",
                    "meta_id": extra["meta_id"],
                    "expected_source_id": want,
                    "target_page": str(tpath.relative_to(REPO)),
                    "collection_file": str(cfile.relative_to(REPO)),
                })
        elif kind == "dingdi":
            # articles 页需反指该采集目录：src-local-html resource 含采集目录名
            resources = resource_lines(tpath)
            cdir_name = cdir.name  # 如 2020-08-27_明日周五操作策略——顶底之王（8月28日）
            if not any(cdir_name in r for r in resources):
                report["back_missing"].append({
                    "collector": "dingdi",
                    "collection_dir": cdir_name,
                    "target_page": str(tpath.relative_to(REPO)),
                    "collection_file": str(cfile.relative_to(REPO)),
                })

    # ---- 孤儿：知识层 topics/articles 页无人指向 ----
    targeted = {str(p) for p in target_to_sources.keys()}
    orphan_topics_real = []
    orphan_topics_videofed = []   # 聚合 BV 视频源，非文章动态喂入 → 正常
    for md in sorted(JEWELRY_TOPICS.glob("*.md")):
        if md.name == "index.md":
            continue
        if str(md) not in targeted:
            ids = source_ids(md) or []
            if any(i.startswith("BV") for i in ids):
                orphan_topics_videofed.append(str(md.relative_to(REPO)))
            else:
                orphan_topics_real.append(str(md.relative_to(REPO)))
    report["orphan_topics"] = orphan_topics_real
    report["orphan_topics_videofed"] = orphan_topics_videofed
    report["orphan_articles"] = []
    for md in sorted(STOCK_ARTICLES.glob("*.md")):
        if md.name == "index.md":
            continue
        if str(md) not in targeted:
            report["orphan_articles"].append(str(md.relative_to(REPO)))

    # ---- 结论汇总 ----
    dup_topics = {k: v for k, v in report["fwd_dup"].items() if "/topics/" in k}
    dup_articles = {k: v for k, v in report["fwd_dup"].items() if "/articles/" in k}

    report["summary"] = {
        "forward_total": report["forward_total"],
        "fwd_missing_count": len(report["fwd_missing"]),
        "back_missing_count": len(report["back_missing"]),
        "orphan_topics_count": len(report["orphan_topics"]),
        "orphan_topics_videofed_count": len(report["orphan_topics_videofed"]),
        "orphan_articles_count": len(report["orphan_articles"]),
        "dup_targets_count": len(report["fwd_dup"]),
        "dup_targets_in_articles": len(dup_articles),
        "parse_warn_count": len(report["parse_warn"]),
        "closed_bidirectional": (
            report["forward_total"]
            - len(report["fwd_missing"])
            - len(report["back_missing"])
        ),
    }

    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    s = report["summary"]
    print("=" * 64)
    print("fused_into 双向指针对账报告")
    print("=" * 64)
    print(f"forward 指针总数        : {s['forward_total']}  "
          f"(老许 {report['forward_by_source'].get('laoxu_meta.json',0)} + "
          f"顶底 {report['forward_by_source'].get('dingdi_article.json',0)})")
    print(f"悬空(目标不存在)        : {s['fwd_missing_count']}")
    print(f"缺反向背书              : {s['back_missing_count']}")
    print(f"孤儿 topics 页          : {s['orphan_topics_count']}  "
          f"(另有视频喂入聚合页 {s['orphan_topics_videofed_count']}，正常)")
    print(f"孤儿 articles 页        : {s['orphan_articles_count']}")
    print(f"重复指针目标            : {s['dup_targets_count']}  "
          f"(其中 articles 多对一异常 {s['dup_targets_in_articles']})")
    print(f"解析警告                : {s['parse_warn_count']}")
    print(f"双向闭合(forward 有效)  : {s['closed_bidirectional']} / {s['forward_total']}")
    print("-" * 64)
    if report["fwd_missing"]:
        print("[悬空] fused_into 指向不存在的文件：")
        for x in report["fwd_missing"]:
            print(f"  - {x['collection_file']} -> {x['resolved_target']}")
    if report["back_missing"]:
        print("[缺反向背书] 知识层未反指采集源：")
        for x in report["back_missing"][:50]:
            print(f"  - {x['target_page']}  <-- 采集 {x['collection_file']}")
        if len(report["back_missing"]) > 50:
            print(f"  ... 其余 {len(report['back_missing'])-50} 条见 --json")
    if report["orphan_topics"]:
        print("[孤儿 topics] 无采集源指向：")
        for x in report["orphan_topics"]:
            print(f"  - {x}")
    if report.get("orphan_topics_videofed"):
        print("[视频喂入聚合 topics]（无文章动态指向，由视频层喂入，正常）：")
        for x in report["orphan_topics_videofed"]:
            print(f"  - {x}")
    if report["orphan_articles"]:
        print("[孤儿 articles] 无采集源指向：")
        for x in report["orphan_articles"]:
            print(f"  - {x}")
    if report["parse_warn"]:
        print("[解析警告]：")
        for x in report["parse_warn"]:
            print(f"  - {x}")
    if not (report["fwd_missing"] or report["back_missing"]
            or report["orphan_topics"] or report["orphan_articles"]):
        print("结论：双向指针完整闭合，无悬空/缺失/孤儿。")
    print("=" * 64)


if __name__ == "__main__":
    main()
