#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doc_health_check.py — 仓库自描述体检（纯标准库，仓库根运行）

让"只给仓库路径就能接手"可执行验证：
  1. 核心文件齐备（冷启动链可达）
  2. Markdown 相对链接不断链
  3. docs/ 下文档都在 DOCUMENTATION_MAP 登记
  4. 禁入内容未进 git（原始音视频/PDF/Office、明文凭证/临时票据；.secrets 仅允许 .enc）
  5. 正式文档无占位词残留（WARN，不阻塞）

退出码：出现 ERROR 返回 1；仅 WARN 返回 0。
用法：python3 scripts/doc_health_check.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ERRORS: list[str] = []
WARNS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNS.append(msg)


def git_ls_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except Exception:  # noqa: BLE001
        return []
    return [p for p in out.splitlines() if p]


# 1. 核心文件齐备 -----------------------------------------------------------
CORE_FILES = [
    "README.md",
    "AGENTS.md",
    "docs/DOCUMENTATION_MAP.md",
    "docs/DIRECTORY_STRUCTURE.md",
    "docs/WORKFLOW.md",
    "docs/REQUIREMENTS.md",
    "docs/ROADMAP.md",
    "docs/项目维护SOP.md",
    "docs/新窗口接手开场白.md",
    "docs/HANDOFF.md",
    "project-management/active/TASK_STATUS.md",
    "project-management/active/ISSUES.md",
    "scripts/doc_health_check.py",
]


def check_core_files() -> None:
    for rel in CORE_FILES:
        if not (ROOT / rel).exists():
            err(f"[核心文件缺失] {rel}")


# 2. Markdown 相对链接 ------------------------------------------------------
# 工程/治理文档断链 = ERROR（接手链必须可达）；library 知识成品断链 = WARN（属内容质检）
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIX = ("http://", "https://", "mailto:", "tel:", "#", "plugin:")


def check_markdown_links() -> None:
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or ".venv" in md.parts or "node_modules" in md.parts:
            continue
        rel = str(md.relative_to(ROOT))
        is_content = rel.startswith(("library/", "workspace/"))
        text = md.read_text(encoding="utf-8", errors="ignore")
        for raw in LINK_RE.findall(text):
            target = raw.split()[0].strip() if raw.split() else raw.strip()
            target = target.split("#", 1)[0]
            if not target or target.startswith(SKIP_PREFIX):
                continue
            # 相对当前文件目录 或 仓库根，二者居其一即通过（容错根相对写法）
            if (md.parent / target).exists() or (ROOT / target).exists():
                continue
            if is_content:
                warn(f"[成品断链] {rel} -> {raw}（知识成品内部链接，属内容质检，不阻塞提交）")
            else:
                err(f"[断链] {rel} -> {raw}")


# 3. docs/ 文档登记覆盖 -----------------------------------------------------
# docs/README.md 是目录说明，由 DOCUMENTATION_MAP 的目录描述覆盖，豁免逐文件登记
REGISTER_EXEMPT = {"docs/README.md"}


def check_docs_registered() -> None:
    map_path = ROOT / "docs/DOCUMENTATION_MAP.md"
    if not map_path.exists():
        return
    map_text = map_path.read_text(encoding="utf-8", errors="ignore")
    for md in (ROOT / "docs").rglob("*.md"):
        rel = str(md.relative_to(ROOT))
        if rel in REGISTER_EXEMPT:
            continue
        if md.name not in map_text:
            err(f"[未登记] {rel} 未在 docs/DOCUMENTATION_MAP.md 登记")


# 4. 禁入内容未进 git -------------------------------------------------------
BANNED_EXT = {
    ".mp4", ".mov", ".mkv", ".flv", ".avi", ".wmv", ".ts", ".m3u8",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".7z", ".rar",
}
# 真实临时票据/明文密钥：参数名后跟足够长的实值（模板里是 <占位>，不会命中）
SECRET_PATTERNS = [
    re.compile(r"exportkey=[A-Za-z0-9%_\-]{12,}"),
    re.compile(r"pass_ticket=[A-Za-z0-9%_\-]{12,}"),
    re.compile(r"sessionInfo=[A-Za-z0-9%_+\-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"***REMOVED***"),
]
SCAN_TEXT_EXT = {".md", ".py", ".go", ".sh", ".js", ".json", ".txt", ".yaml", ".yml"}


def check_git_hygiene() -> None:
    tracked = git_ls_files()
    if not tracked:
        warn("[git] 未取到 git 跟踪文件清单，跳过入库检查")
        return
    for rel in tracked:
        p = ROOT / rel
        suffix = p.suffix.lower()
        # .secrets 只允许 .enc / .gitignore / 说明
        if rel.startswith(".secrets/"):
            if not (suffix == ".enc" or p.name in {".gitignore", "README.md"}):
                err(f"[凭证非加密入库] .secrets 下仅允许 .enc：{rel}")
        # 禁入扩展名
        if suffix in BANNED_EXT:
            err(f"[禁入文件类型入库] {rel}")
        # capture/manifest 类含票据的 json
        low = rel.lower()
        if suffix == ".json" and ("capture" in low or "finder_" in low):
            err(f"[疑似含票据的捕获产物入库] {rel}")
        # 明文票据内容扫描（跳过本脚本自身，其内含检测模式）
        if suffix in SCAN_TEXT_EXT and not rel.endswith("doc_health_check.py"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:  # noqa: BLE001
                continue
            for pat in SECRET_PATTERNS:
                m = pat.search(text)
                if m:
                    err(f"[明文凭证/票据] {rel} 命中 {m.group(0)[:24]}…")
                    break


# 5. 占位词（WARN） ---------------------------------------------------------
PLACEHOLDER = ["TBD", "TODO", "XXX", "待补充", "待完善", "占位符", "lorem"]
# 豁免：活态台账/日志/评审/专项任务档，以及"专门检查占位词"的清单本身
PLACEHOLDER_EXEMPT_SUBSTR = (
    "TASK_STATUS", "ISSUES", "HANDOFF", "reviews", "-task.md", "DOC_SYNC_CHECKLIST",
)


def check_placeholders() -> None:
    for scope in [ROOT / "docs", ROOT / "project-management"]:
        if not scope.exists():
            continue
        for md in scope.rglob("*.md"):
            rel = str(md.relative_to(ROOT))
            if any(x in rel for x in PLACEHOLDER_EXEMPT_SUBSTR):
                continue
            text = md.read_text(encoding="utf-8", errors="ignore")
            for word in PLACEHOLDER:
                if word in text:
                    warn(f"[占位词] {rel} 含 '{word}'，确认是否待补")
                    break


def main() -> int:
    check_core_files()
    check_markdown_links()
    check_docs_registered()
    check_git_hygiene()
    check_placeholders()

    print("=" * 64)
    print("文档体检 doc_health_check")
    print("=" * 64)
    for e in ERRORS:
        print(f"  ERROR  {e}")
    for w in WARNS:
        print(f"  WARN   {w}")
    print("-" * 64)
    print(f"ERROR {len(ERRORS)} 项 / WARN {len(WARNS)} 项")
    if ERRORS:
        print("❌ 体检未通过：修复全部 ERROR 后再提交")
        return 1
    print("✅ 0 ERROR，可以提交（WARN 请知悉）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
