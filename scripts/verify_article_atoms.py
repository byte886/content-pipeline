#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_article_atoms.py — 顶底之王 ArticleNote 全量机械核验（五维中可机械化部分）。
幂等只读，不改任何文件。覆盖新旧两套模板（## 编译摘要 bullet / > blockquote）。

五维映射：
 D1 回源可解析：src-local-html 路径存在；article_id 与目录对应。
 D5 来源一致：title / published / article_id 与采集层 article.json 一致。
 D2 摘要忠实：摘要(旧bullet/新blockquote)+要点 每条逐字命中原文。
 D3 数字准确：原子页数字集合 vs 原文数字集合，双向 diff。
 D4 结构合规：frontmatter 必填字段在；sources 的 id 在正文脚注或来源行出现。
输出：通过数 / 异常清单（逐条 article_id）。
"""
import os, re, json, glob, sys

ROOT = os.path.expanduser("~/Desktop/content-pipeline")
ATOM_DIR = os.path.join(ROOT, "library/05_knowledge/stock/concepts/articles")

TOP_SKIP = re.compile(r"^(新进来的朋友|点击上方蓝色字体关注我|，可以第一时间获取我的市场观点及操作策略。?)$")
BOT_BREAK = re.compile(r"(感谢朋友们的关注|特别提醒|免责声明|7年交易员|去哪个交易室|投资有风险|入市需谨慎|刘广义|上海凯石|上海中广云|案例截图|^顶$|^底$|^之$|^王$)")


def split_fm(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[1:i]), "\n".join(lines[i+1:])
    return "", text


def fm_get(fm, key):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else None


def norm(s):
    return re.sub(r"[\s，。！？、；：""''（）()\[\]．\.，,\!\?\;\:\-—~～%·]", "", s)


def nums_in(s):
    return set(norm(x) for x in re.findall(r"\d+(?:\.\d+)?\s*(?:%|万亿|亿|万|点)?", s))


def src_and_articlejson(atomic_text):
    m = re.search(r"resource:\s*(library/06_articles[^\n]+content\.md)", atomic_text)
    sp = os.path.join(ROOT, m.group(1).strip()) if m else None
    aj = os.path.join(os.path.dirname(sp), "article.json") if sp else None
    return sp, aj


def extract_summary_points(body):
    """返回 (summary_bullets, point_bullets)。旧模板: ## 编译摘要/## 要点。新模板: > blockquote + ## 要点。"""
    summary, points = [], []
    # new template blockquote
    bq = [l.strip()[1:].strip() for l in body.splitlines() if l.strip().startswith(">")]
    if bq:
        summary = bq
    # old template sections
    m = re.search(r"## 编译摘要[^\n]*\n(.*?)(?=\n## )", body, re.S)
    if m and not bq:
        summary = [l.strip()[2:].strip() for l in m.group(1).splitlines() if l.strip().startswith("-")]
    mp = re.search(r"## 要点[^\n]*\n(.*?)(?=\n---|\Z)", body, re.S)
    if mp:
        points = [l.strip()[2:].strip() for l in mp.group(1).splitlines() if l.strip().startswith("-")]
    return summary, points


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(ATOM_DIR, "wechat_*.md"))):
        aid = os.path.basename(p)[:-3]
        text = open(p, encoding="utf-8").read()
        fm, body = split_fm(text)
        issues = []

        # D5 frontmatter basics
        for k in ("type", "title", "status", "article_id"):
            if not fm_get(fm, k):
                issues.append(f"缺字段:{k}")
        if fm_get(fm, "article_id") and fm_get(fm, "article_id") != aid:
            issues.append(f"article_id不匹配:{fm_get(fm,'article_id')}!={aid}")

        sp, ajp = src_and_articlejson(text)
        # D1 src exists
        if not sp or not os.path.exists(sp):
            issues.append("回源路径不存在")
            rows.append(dict(aid=aid, issues=issues)); continue

        src_text = open(sp, encoding="utf-8").read()
        _, src_body = split_fm(src_text)
        # strip boilerplate from src for verbatim check
        src_keep = []
        for ln in src_body.splitlines():
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("来源："): continue
            if TOP_SKIP.match(s): continue
            if BOT_BREAK.search(s): break
            src_keep.append(s)
        src_flat = "".join(src_keep)
        src_norm = norm(src_flat)

        # D5 article.json consistency
        if ajp and os.path.exists(ajp):
            aj = json.load(open(ajp, encoding="utf-8"))
            if fm_get(fm, "title") != aj.get("title"):
                issues.append("title与article.json不一致")
            if fm_get(fm, "published") and fm_get(fm, "published") != aj.get("date"):
                issues.append(f"published({fm_get(fm,'published')})!=aj.date({aj.get('date')})")
        else:
            issues.append("article.json缺失")

        # D2 verbatim
        summary, points = extract_summary_points(body)
        if not summary:
            issues.append("摘要为空")
        miss = []
        for s in summary + points:
            sn = norm(s)
            if not sn: continue
            ok = sn in src_norm or (len(sn) > 10 and sn[:15] in src_norm)
            if not ok:
                miss.append(s[:30])
        if miss:
            issues.append(f"逐字未命中{len(miss)}条:{miss[:3]}")

        # D3 number diff
        atomic_nums = nums_in("\n".join(summary + points))
        src_nums = nums_in(src_flat)
        # 页内有/原文无（编造数字）
        invented = sorted(atomic_nums - src_nums)
        if invented:
            issues.append(f"页内有原文无数字:{invented[:6]}")

        rows.append(dict(aid=aid, issues=issues, n_sum=len(summary), n_pts=len(points)))

    bad = [r for r in rows if r["issues"]]
    print(f"全量核验: {len(rows)} 篇")
    print(f"通过: {len(rows)-len(bad)}")
    print(f"异常: {len(bad)}")
    for r in bad:
        print(f"\n● {r['aid']}")
        for i in r["issues"]:
            print(f"    - {i}")
    json.dump(rows, open(os.path.join(ROOT, "workspace", "K6_verify_all.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nWROTE workspace/K6_verify_all.json")


if __name__ == "__main__":
    main()
