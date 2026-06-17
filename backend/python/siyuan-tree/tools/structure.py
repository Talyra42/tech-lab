#!/usr/bin/env python3
"""导出思源笔记本的文档结构（树 / JSON / Markdown）。

用法：
  uv run python tools/structure.py                 # 全部笔记本，纯文本树
  uv run python tools/structure.py -f markdown     # Markdown 列表（最适合喂给 AI）
  uv run python tools/structure.py -f json         # JSON
  uv run python tools/structure.py -n 后端学习      # 只导出名字含「后端学习」的笔记本
  uv run python tools/structure.py -f markdown -o tree.md   # 另存到 output/tree.md

输出同时打印到 stdout，并写入 output/（res.txt / res.json / res.md）。
"""

import argparse
import json
import os

from rich.console import Console
from rich.tree import Tree

import siyuan

DEFAULT_NAMES = {"tree": "res.txt", "json": "res.json", "markdown": "res.md"}


def collect_docs(notebook_id: str, parent_path: str, depth: int) -> list:
    """递归收集某路径下的直接子文档，返回嵌套结构。"""
    if depth >= siyuan.MAX_DEPTH:
        return []
    p = siyuan.esc(parent_path.rstrip("/"))
    # 直接子级：匹配 /parent/% 但不含更深一层的 /
    rows = siyuan.sql(f"""
        SELECT id, hpath, content
        FROM   blocks
        WHERE  type = 'd' AND box = '{siyuan.esc(notebook_id)}'
          AND  hpath LIKE '{p}/%'
          AND  hpath NOT LIKE '{p}/%/%'
        ORDER  BY hpath
    """)
    nodes = []
    for doc in rows:
        nodes.append({
            "id": doc["id"],
            "title": siyuan.doc_title(doc),
            "path": doc["hpath"],
            "children": collect_docs(notebook_id, doc["hpath"], depth + 1),
        })
    return nodes


def collect(notebooks: list) -> dict:
    return {
        "notebooks": [
            {
                "id": nb["id"],
                "name": nb.get("name", nb["id"]),
                "docs": collect_docs(nb["id"], "/", 1),
            }
            for nb in notebooks
        ]
    }


# ── 渲染器 ────────────────────────────────────────

def _add_to_tree(parent: Tree, docs: list):
    for doc in docs:
        node = parent.add(f"[white]{doc['title']}[/white]")
        _add_to_tree(node, doc["children"])


def render_tree(data: dict, target: Console):
    for nb in data["notebooks"]:
        tree = Tree(f"[bold green]📓 {nb['name']}[/bold green]")
        _add_to_tree(tree, nb["docs"])
        target.print(tree)
        target.print()


def render_tree_text(data: dict) -> str:
    plain = Console(color_system=None)
    with plain.capture() as cap:
        render_tree(data, plain)
    return cap.get().rstrip("\n")


def render_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _md_lines(docs: list, depth: int) -> list:
    lines = []
    for doc in docs:
        lines.append("  " * depth + f"- {doc['title']}")
        lines.extend(_md_lines(doc["children"], depth + 1))
    return lines


def render_markdown(data: dict) -> str:
    blocks = []
    for nb in data["notebooks"]:
        lines = [f"# {nb['name']}", ""]
        lines.extend(_md_lines(nb["docs"], 0))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def parse_args():
    parser = argparse.ArgumentParser(description="导出思源笔记的文档结构")
    parser.add_argument("-f", "--format", choices=["tree", "json", "markdown"],
                        default="tree", help="输出格式（默认 tree）")
    parser.add_argument("-n", "--notebook", metavar="KEYWORD",
                        help="只导出名字包含该关键词的笔记本（默认全部）")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="输出文件名（默认 res.txt/json/md，均存入 output/）")
    return parser.parse_args()


def main():
    args = parse_args()
    siyuan.init()

    siyuan.err.print("[cyan]正在连接思源笔记……[/cyan]")
    notebooks = siyuan.get_notebooks()
    if args.notebook:
        notebooks = [nb for nb in notebooks if args.notebook in nb.get("name", "")]
    if not notebooks:
        siyuan.err.print("[yellow]未找到匹配的笔记本。[/yellow]")
        return

    data = collect(notebooks)

    if args.format == "json":
        text = render_json(data)
        print(text)
    elif args.format == "markdown":
        text = render_markdown(data)
        print(text)
    else:  # tree：终端彩色，文件纯文本
        render_tree(data, siyuan.console)
        text = render_tree_text(data)

    filename = os.path.basename(args.output) if args.output else DEFAULT_NAMES[args.format]
    os.makedirs(siyuan.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(siyuan.OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    siyuan.err.print(f"[bold green]✓ 已写入 {path}[/bold green]（共 {len(notebooks)} 个笔记本）")


if __name__ == "__main__":
    main()
