from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"
DRAFTS_DIR = REPO_ROOT / "drafts"
MKDOCS_YML = REPO_ROOT / "mkdocs.yml"


@dataclass(frozen=True)
class Article:
    root: Path
    relpath: Path

    @property
    def abspath(self) -> Path:
        return self.root / self.relpath

    @property
    def is_markdown(self) -> bool:
        return self.relpath.suffix.lower() == ".md"


def _iter_md_files(root: Path) -> list[Path]:
    if not root.exists():
        return []

    paths: list[Path] = []
    for path in root.rglob("*.md"):
        if path.is_file():
            paths.append(path)
    return sorted(paths, key=lambda p: str(p).lower())


def _articles_in_docs() -> list[Article]:
    if not DOCS_DIR.exists():
        return []

    reserved = {Path("index.md"), Path("about.md")}
    articles: list[Article] = []
    for md in _iter_md_files(DOCS_DIR):
        rel = md.relative_to(DOCS_DIR)
        if rel in reserved:
            continue
        articles.append(Article(DOCS_DIR, rel))
    return articles


def _articles_in_drafts() -> list[Article]:
    if not DRAFTS_DIR.exists():
        return []
    return [Article(DRAFTS_DIR, p.relative_to(DRAFTS_DIR)) for p in _iter_md_files(DRAFTS_DIR)]


def _read_title(md_path: Path) -> str:
    try:
        for line in md_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass

    name = md_path.stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(w[:1].upper() + w[1:] for w in name.split() if w)


def _prompt_indices(items: list[str], prompt: str) -> list[int]:
    if not items:
        return []

    for idx, item in enumerate(items, start=1):
        print(f"{idx:>2}. {item}")

    raw = input(prompt).strip()
    if not raw:
        return []
    if raw.lower() in {"q", "quit", "exit"}:
        raise SystemExit(0)

    indices: set[int] = set()
    for part in re.split(r"[,\s]+", raw):
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start > end:
                start, end = end, start
            for i in range(start, end + 1):
                indices.add(i)
        else:
            indices.add(int(part))

    resolved = sorted(i for i in indices if 1 <= i <= len(items))
    if not resolved:
        raise ValueError("No valid selections.")
    return resolved


def _move_article(src_root: Path, dst_root: Path, relpath: Path, *, force: bool) -> None:
    src = src_root / relpath
    dst = dst_root / relpath
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        if not force:
            raise FileExistsError(f"Destination exists: {dst}")
        if dst.is_dir():
            raise IsADirectoryError(f"Destination is a directory: {dst}")
        dst.unlink()

    shutil.move(str(src), str(dst))


def _render_nav_yaml() -> str:
    def section_items(section_dir: Path) -> list[tuple[str, str]]:
        if not section_dir.exists():
            return []
        items: list[tuple[str, str]] = []
        for md in _iter_md_files(section_dir):
            rel = md.relative_to(DOCS_DIR).as_posix()
            title = _read_title(md)
            items.append((title, rel))
        return items

    llm_items = section_items(DOCS_DIR / "llm")
    agent_items = section_items(DOCS_DIR / "agents")
    science_items = section_items(DOCS_DIR / "ai_for_science")

    lines: list[str] = []
    lines.append("nav:")
    lines.append("  - Home: index.md")
    if llm_items:
        lines.append("  - LLM Notes:")
        for title, rel in llm_items:
            lines.append(f"      - {title}: {rel}")
    if agent_items:
        lines.append("  - Agent Architectures:")
        for title, rel in agent_items:
            lines.append(f"      - {title}: {rel}")
    if science_items:
        lines.append("  - AI for Science:")
        for title, rel in science_items:
            lines.append(f"      - {title}: {rel}")
    lines.append("  - About: about.md")
    return "\n".join(lines) + "\n"


def _update_mkdocs_nav() -> None:
    if not MKDOCS_YML.exists():
        raise FileNotFoundError(f"Missing {MKDOCS_YML.name} in repo root.")

    text = MKDOCS_YML.read_text(encoding="utf-8")
    match = re.search(r"(?m)^nav:\s*$", text)
    nav_yaml = _render_nav_yaml()

    if not match:
        if not text.endswith("\n"):
            text += "\n"
        MKDOCS_YML.write_text(text + "\n" + nav_yaml, encoding="utf-8")
        return

    MKDOCS_YML.write_text(text[: match.start()] + nav_yaml, encoding="utf-8")


def _list() -> int:
    print("Published (docs/):")
    published = _articles_in_docs()
    if not published:
        print("  (none)")
    else:
        for a in published:
            print(f"  - {a.relpath.as_posix()}")

    print("\nDrafts (drafts/):")
    drafts = _articles_in_drafts()
    if not drafts:
        print("  (none)")
    else:
        for a in drafts:
            print(f"  - {a.relpath.as_posix()}")
    return 0


def _interactive(force: bool) -> int:
    DRAFTS_DIR.mkdir(exist_ok=True)

    print("Choose an action:")
    print("  1) Unpublish (move docs/ -> drafts/)")
    print("  2) Publish   (move drafts/ -> docs/)")
    print("  3) List")
    choice = input("Enter 1/2/3 (or q): ").strip().lower()
    if choice in {"q", "quit", "exit"}:
        return 0
    if choice == "3":
        return _list()

    if choice == "1":
        src_root, dst_root = DOCS_DIR, DRAFTS_DIR
        src_items = _articles_in_docs()
        label = "Unpublish"
    elif choice == "2":
        src_root, dst_root = DRAFTS_DIR, DOCS_DIR
        src_items = _articles_in_drafts()
        label = "Publish"
    else:
        print("Invalid choice.", file=sys.stderr)
        return 2

    if not src_items:
        print(f"No articles available to {label.lower()}.")
        return 0

    display = [a.relpath.as_posix() for a in src_items]
    try:
        picked = _prompt_indices(display, "Select items (e.g. 1 2 5-7), Enter to cancel: ")
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    for idx in picked:
        article = src_items[idx - 1]
        _move_article(src_root, dst_root, article.relpath, force=force)
        print(f"{label}ed: {article.relpath.as_posix()}")

    _update_mkdocs_nav()
    print("Updated mkdocs nav.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Publish/unpublish MkDocs articles by moving .md files between docs/ and drafts/.",
    )
    parser.add_argument("--list", action="store_true", help="List published and draft articles.")
    parser.add_argument("--force", action="store_true", help="Overwrite destination files if they exist.")
    args = parser.parse_args(argv)

    if args.list:
        return _list()
    return _interactive(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

