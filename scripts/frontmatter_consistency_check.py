#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frontmatter_consistency_check.py — frontmatter ↔ 正文一致性检查（只读）

范围：library/05_knowledge/{jewelry,stock}/concepts/{books,videos,articles,topics,reports}
     （不含 courses/，课程清洗由并行代理负责）。

检查三类不一致：
  UNDEFINED_DEF  正文有脚注定义 [^id]: ，但 frontmatter sources 里没有该 id 背书
                 （脚注成了无来源背书的"野脚注"）
  ORPHAN_SOURCE  frontmatter 声明了 source id，但正文既无脚注定义也无内联引用
                 （声明了来源却从头到尾没被正文用到）
  DANGLING_REF   正文内联 [^id] 被引用，但既无脚注定义也无 source 背书
                 （读者点进去是空锚）

说明：
  - BookNote 的 src-book 只有"指向提取物"的脚注定义行（原子指针惯例），
    不算 ORPHAN_SOURCE（有定义即视为有背书）。
  - ArticleNote/ReportNote 的 sources 是采集来源背书（src-wechat/src-local-html/
    src-source/src-manifest），正文不做行内引用属设计约定；本脚本仍报告其
    source 是否完全无脚注挂钩，供人工判断，不直接判错。

退出码恒 0（只读检查）。
用法：python3 scripts/frontmatter_consistency_check.py [--json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KNOW = REPO / "library" / "05_knowledge"

DIRS = ["books", "videos", "articles", "topics", "reports"]

FM_SPLIT_RE = re.compile(r"^---\s*$")
# sources[].id：兼容块式 '- id: x' 与流式 '{ id: "x" }'
SRC_ID_RE = re.compile(r"(?:^|[-{]\s+)id:\s*[\"']?([^\"'\n,}]+?)[\"']?\s*[,}\n]", re.M)
TYPE_RE = re.compile(r"^type:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", re.M)
# 脚注定义：行首 [^id]:
FN_DEF_RE = re.compile(r"^\[\^([^\]\s]+)\]\s*:")
# 内联脚注引用：[^id]（行内，非定义行）
FN_REF_RE = re.compile(r"\[\^([^\]\s]+)\]")


def split_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    body_lines = []
    fm = []
    started = False
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---" and not started:
            started = True
            continue
        if not started:
            fm.append(ln)
        else:
            body_lines.append(ln)
    return "\n".join(fm), "\n".join(body_lines)


def analyze(md: Path):
    text = md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    src_ids = [s.strip() for s in SRC_ID_RE.findall(fm)]
    mtype = (TYPE_RE.search(fm) or [None, "Unknown"])[1] if TYPE_RE.search(fm) else "Unknown"

    defs = {}
    inline_refs = set()
    for ln in body.splitlines():
        d = FN_DEF_RE.match(ln)
        if d:
            defs[d.group(1)] = ln.strip()
            continue
        for r in FN_REF_RE.findall(ln):
            inline_refs.add(r)

    issues = []
    # UNDEFINED_DEF
    for d in defs:
        if d not in src_ids:
            issues.append(("UNDEFINED_DEF", d))
    # ORPHAN_SOURCE：声明的 source 既无 def 也无内联引用
    for s in src_ids:
        if s not in defs and s not in inline_refs:
            issues.append(("ORPHAN_SOURCE", s))
    # DANGLING_REF：内联引用既无 def 也无 source
    for r in inline_refs:
        if r not in defs and r not in src_ids:
            issues.append(("DANGLING_REF", r))

    return {
        "file": str(md.relative_to(REPO)),
        "type": mtype,
        "src_ids": src_ids,
        "defs": sorted(defs.keys()),
        "inline": sorted(inline_refs),
        "issues": issues,
    }


def main():
    results = []
    for industry in ["jewelry", "stock"]:
        for d in DIRS:
            base = KNOW / industry / "concepts" / d
            if not base.exists():
                continue
            for md in sorted(base.glob("*.md")):
                if md.name in ("index.md", "log.md"):
                    continue
                results.append(analyze(md))

    bad = [r for r in results if r["issues"]]
    # 统计
    by_kind = {"UNDEFINED_DEF": [], "ORPHAN_SOURCE": [], "DANGLING_REF": []}
    for r in bad:
        for kind, ref in r["issues"]:
            by_kind[kind].append({"file": r["file"], "type": r["type"], "ref": ref})

    summary = {
        "files_scanned": len(results),
        "files_with_issues": len(bad),
        "by_type": {},
        "counts": {k: len(v) for k, v in by_kind.items()},
    }
    for r in results:
        summary["by_type"].setdefault(r["type"], 0)
        summary["by_type"][r["type"]] += 1

    payload = {"summary": summary, "issues": by_kind, "files_with_issues": [r["file"] for r in bad]}

    if "--json" in sys.argv:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("=" * 64)
    print("frontmatter ↔ 正文一致性检查报告")
    print("=" * 64)
    print(f"扫描文件数        : {summary['files_scanned']}")
    print(f"按类型分布        : {summary['by_type']}")
    print(f"存在不一致文件数  : {summary['files_with_issues']}")
    print(f"  UNDEFINED_DEF  (脚注无 source 背书) : {summary['counts']['UNDEFINED_DEF']}")
    print(f"  ORPHAN_SOURCE  (声明 source 未被引用): {summary['counts']['ORPHAN_SOURCE']}")
    print(f"  DANGLING_REF   (内联引用空锚)      : {summary['counts']['DANGLING_REF']}")
    print("-" * 64)
    for kind in ["UNDEFINED_DEF", "DANGLING_REF", "ORPHAN_SOURCE"]:
        lst = by_kind[kind]
        if not lst:
            continue
        print(f"[{kind}] {len(lst)} 条：")
        for it in lst[:60]:
            print(f"  - {it['file']}  ({it['type']})  ref={it['ref']}")
        if len(lst) > 60:
            print(f"  ... 其余 {len(lst)-60} 条见 --json")
    if not bad:
        print("结论：无不一致。")
    print("=" * 64)


if __name__ == "__main__":
    main()
