#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_stale_after_dingdi.py — 顶底之王 ArticleNote stale_after 受控回填（只增不删）

范围：library/05_knowledge/stock/concepts/articles/*.md（content_type: market_view/howto）
规则：行情/点位类原子页为强时效市场评论，统一补 stale_after=2027-01-01T23:59:59+08:00
      （未来复审日；不触发 W31/W32；不补 verified——机器摘要未人工核）。
幂等：已有 stale_after 的跳过。
只增：只在 status: draft 行后插入一行，不删除/不改写任何既有行。
记录：输出原始值(无)→新值清单到 stdout。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ART = REPO / "library" / "05_knowledge" / "stock" / "concepts" / "articles"

STALE = "2027-01-01T23:59:59+08:00"


def main():
    changed, skipped = [], []
    for md in sorted(ART.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if "stale_after:" in text.split("---", 2)[1]:
            skipped.append((md.name, "已有 stale_after"))
            continue
        lines = text.splitlines()
        out = []
        inserted = False
        for ln in lines:
            out.append(ln)
            if not inserted and ln.strip() == "status: draft":
                out.append(f"stale_after: {STALE}")
                inserted = True
        if not inserted:
            skipped.append((md.name, "未找到 status: draft 锚点"))
            continue
        md.write_text("\n".join(out) + "\n", encoding="utf-8")
        changed.append(md.name)

    print(f"回填 stale_after 文件数 : {len(changed)}")
    print(f"跳过文件数            : {len(skipped)}")
    print(f"统一取值             : {STALE}")
    print("原始值 -> 新值 : (无 stale_after) -> stale_after")
    for n in changed:
        print(f"  + {n}")
    if skipped:
        print("跳过：")
        for n, why in skipped:
            print(f"  - {n} ({why})")


if __name__ == "__main__":
    main()
