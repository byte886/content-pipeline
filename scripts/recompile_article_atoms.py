#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recompile_article_atoms.py — 顶底之王 ArticleNote 原子页「折行归并 + 重编译」工具（阶段一）

背景：采集层 content.md 在 2024-2026（及部分 2021-2022）把一句话按 OCR 折行拆成
多行（标点/数字独立成行），导致旧抽取器：①丢掉独立成行的数字；②把一句切成多条碎片；
③编译摘要为空。本工具：
  1) 只读解析 content.md，跳过顶部引导语、在底部免责/签名处截断；
  2) 把折行碎片拼接回完整句子，再按句末标点重新切句；
  3) 重编译知识层原子页正文：编译摘要 1-2 句 + 要点 4 句（全部逐字来自原文，数字完整）。

红线：绝不改写 06_articles 原文 content.md；只重编译 05_knowledge 知识层原子页正文；
frontmatter 除 description 外全部保留（status/verified/ai_checked/stale_after 不回退）。

用法：
  python3 scripts/recompile_article_atoms.py --scan           # 只扫描，打印折行分布
  python3 scripts/recompile_article_atoms.py --apply          # 备份+重编译折行页（幂等）
  python3 scripts/recompile_article_atoms.py --apply --dry-run
"""
import os, re, sys, json, glob, shutil, argparse, datetime

ROOT = os.path.expanduser("~/Desktop/content-pipeline")
ATOM_DIR = os.path.join(ROOT, "library/05_knowledge/stock/concepts/articles")
BACKUP_DIR = os.path.join(ROOT, "workspace", "_backup_recompile_20261013")

# 顶部引导语（公众号新粉提示）——跳过，不计入正文
TOP_SKIP = re.compile(r"^(新进来的朋友|点击上方蓝色字体关注我|，可以第一时间获取我的市场观点及操作策略。?)$")
# 底部模板语——其后截断
BOT_BREAK = re.compile(r"(感谢朋友们的关注|特别提醒|免责声明|7年交易员|去哪个交易室|投资有风险|入市需谨慎|刘广义|上海凯石|上海中广云|案例截图|^顶$|^底$|^之$|^王$)")
SENT_SPLIT = re.compile(r"[^。！？]*[。！？]+")


def strip_fm(text):
    """返回 (frontmatter_text_without_dashes, body_text_after_second_dash)"""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[1:i]), "\n".join(lines[i+1:])
    return "", text


def src_path_of(atomic_text):
    m = re.search(r"resource:\s*(library/06_articles[^\n]+content\.md)", atomic_text)
    return os.path.join(ROOT, m.group(1).strip()) if m else None


def extract_sentences(content_path):
    """读 content.md，返回 (joined_line_count, sentences[])。只读。"""
    t = open(content_path, encoding="utf-8").read()
    _, body = strip_fm(t)
    kept = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("来源："):
            continue
        if TOP_SKIP.match(s):
            continue
        if BOT_BREAK.search(s):
            break
        kept.append(s)
    flat = "".join(kept)
    sents = [s.strip() for s in SENT_SPLIT.findall(flat) if len(s.strip()) >= 6]
    return len(kept), sents


def wrap_metrics(content_path):
    t = open(content_path, encoding="utf-8").read()
    _, body = strip_fm(t)
    kept = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("来源："):
            continue
        if TOP_SKIP.match(s):
            continue
        if BOT_BREAK.search(s):
            break
        kept.append(s)
    n = len(kept)
    if n == 0:
        return dict(n=0, wrapped=False)
    short = sum(1 for l in kept if len(l) <= 4)
    numonly = sum(1 for l in kept if re.fullmatch(r"[\d,\.]+%?", l))
    short_ratio = short / n
    wrapped = short_ratio >= 0.35 or (numonly >= 1 and short_ratio >= 0.2)
    return dict(n=n, short_ratio=round(short_ratio, 2), numonly=numonly, wrapped=wrapped)


def build_body(title, sentences):
    """用切好的句子重编译原子页正文。摘要=前1-2句，要点=接下来4句。逐字忠实。"""
    summary = sentences[:2]
    points = sentences[2:6]
    lines = [f"# {title}", "", "## 编译摘要（重编译 2026-10-13：折行归并）", ""]
    for s in summary:
        lines.append(f"- {s}")
    lines += ["", "## 要点", ""]
    for s in points:
        lines.append(f"- {s}")
    return "\n".join(lines), summary


def recompile_atomic(atomic_path, dry=False):
    text = open(atomic_path, encoding="utf-8").read()
    fm, body = strip_fm(text)
    sp = src_path_of(text)
    if not sp or not os.path.exists(sp):
        return "no_src"
    _, sentences = extract_sentences(sp)
    if len(sentences) < 3:
        return "too_few_sentences"
    # title from frontmatter
    mt = re.search(r"^title:\s*(.+)$", fm, re.M)
    title = mt.group(1).strip() if mt else os.path.basename(atomic_path)[:-3]
    new_body_core, summary = build_body(title, sentences)
    # preserve the trailing 来源 footer line(s)
    footer_lines = [ln for ln in body.splitlines() if ln.strip().startswith("来源：")]
    footer = "\n\n---\n\n" + "\n".join(footer_lines) + "\n" if footer_lines else "\n"
    # update description line in frontmatter
    desc_new = "AI重编译：" + summary[0]
    new_fm_lines = []
    for ln in fm.splitlines():
        if ln.startswith("description:"):
            new_fm_lines.append(f'description: "{desc_new}"')
        else:
            new_fm_lines.append(ln)
    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---\n\n" + new_body_core + footer
    if not dry:
        # backup
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(atomic_path, os.path.join(BACKUP_DIR, os.path.basename(atomic_path)))
        open(atomic_path, "w", encoding="utf-8").write(new_text)
    return "recompiled"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages = sorted(glob.glob(os.path.join(ATOM_DIR, "wechat_*.md")))
    wrapped = []
    for p in pages:
        text = open(p, encoding="utf-8").read()
        sp = src_path_of(text)
        if not sp or not os.path.exists(sp):
            continue
        m = wrap_metrics(sp)
        if not m.get("wrapped"):
            continue
        # 仅旧模板（## 编译摘要 bullet）需要重编译；新模板（>blockquote）已正确保留数字
        body = text.split("---", 2)[2] if text.count("---") >= 2 else text
        if "## 编译摘要" not in body:
            continue
        wrapped.append((p, m))

    print(f"扫描原子页总数: {len(pages)}")
    print(f"判定为折行(需重编译): {len(wrapped)}")
    for p, m in wrapped:
        print(f"  {os.path.basename(p):34} n={m['n']:3} short%={m['short_ratio']} num={m['numonly']}")

    if args.scan:
        return
    if not args.apply:
        print("\n(仅扫描。加 --apply 执行重编译；--dry-run 预览不写)")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    cnt = {"recompiled": 0, "no_src": 0, "too_few": 0}
    for p, m in wrapped:
        r = recompile_atomic(p, dry=args.dry_run)
        cnt[r if r in cnt else "recompiled"] = cnt.get(r if r in cnt else "recompiled", 0) + 1
    print(f"\n重编译完成: {cnt}" + ("  [DRY-RUN 未写盘]" if args.dry_run else ""))
    if not args.dry_run:
        print(f"备份目录: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
