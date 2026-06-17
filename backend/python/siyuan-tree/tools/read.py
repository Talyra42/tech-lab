#!/usr/bin/env python3
"""读取思源笔记文档的 Markdown 正文（供 AI 阅读）。

用法：
  uv run python tools/read.py "React Fiber"      # 按标题/路径关键词查找并输出正文
  uv run python tools/read.py --id 20210808...   # 按文档块 ID 直接输出正文
  uv run python tools/read.py -s "Fiber"         # 只列出匹配候选（不输出正文）
  uv run python tools/read.py "Ink" --tree       # 整个主题：该文档 + 全部子文档一起输出

行为：
  - 唯一命中 → 输出该文档 Markdown（首行 <!-- hPath --> 标明路径）
  - 命中多篇 → 列出候选（序号 / 标题 / 路径 / id），再用 --id 精确读
  - --tree   → 连同所有后代文档一并导出，适合整章/整个主题总结
"""

import argparse
import sys

import siyuan


def emit(hpath: str, content: str):
    print(f"<!-- {hpath} -->\n")
    print(content)
    print()


def print_candidates(rows: list):
    siyuan.err.print(f"[yellow]匹配到 {len(rows)} 篇，请用更精确的关键词或 --id 指定其一：[/yellow]")
    for i, row in enumerate(rows, 1):
        siyuan.err.print(
            f"  [cyan]{i:>2}[/cyan]. {siyuan.doc_title(row)}  "
            f"[dim]{row['hpath']}  (id={row['id']})[/dim]"
        )


def read_one(doc_id: str):
    hpath, content = siyuan.export_markdown(doc_id)
    emit(hpath, content)


def read_tree(row: dict):
    """输出该文档及其全部后代文档。"""
    # 先输出根文档
    hpath, content = siyuan.export_markdown(row["id"])
    emit(hpath, content)
    # 再按路径顺序输出后代
    kids = siyuan.descendant_docs(row_box(row), row["hpath"])
    siyuan.err.print(f"[dim]子树共 {len(kids)} 篇子文档[/dim]")
    for kid in kids:
        khpath, kcontent = siyuan.export_markdown(kid["id"])
        emit(khpath, kcontent)


def row_box(row: dict) -> str:
    """从一行文档记录取所属笔记本 box；blocks 查询里带上 box 更稳，这里兜底再查一次。"""
    if row.get("box"):
        return row["box"]
    got = siyuan.sql(f"SELECT box FROM blocks WHERE id = '{siyuan.esc(row['id'])}' LIMIT 1")
    return got[0]["box"] if got else ""


def parse_args():
    parser = argparse.ArgumentParser(description="读取思源笔记文档的 Markdown 正文")
    parser.add_argument("keyword", nargs="?", help="标题或路径关键词")
    parser.add_argument("--id", help="直接指定文档块 ID（跳过搜索）")
    parser.add_argument("-s", "--search", action="store_true", help="只列候选，不输出正文")
    parser.add_argument("-t", "--tree", action="store_true",
                        help="连同所有后代文档一起输出（整个主题）")
    return parser.parse_args()


def resolve_row(doc_id: str) -> dict:
    rows = siyuan.sql(f"SELECT id, hpath, content, box FROM blocks WHERE id = '{siyuan.esc(doc_id)}' LIMIT 1")
    return rows[0] if rows else {"id": doc_id, "hpath": "", "content": ""}


def main():
    args = parse_args()
    siyuan.init()

    # 路径一：直接给了 ID
    if args.id:
        if args.tree:
            read_tree(resolve_row(args.id))
        else:
            read_one(args.id)
        return

    if not args.keyword:
        siyuan.err.print("[yellow]请提供关键词或 --id。用法见 tools/read.py -h[/yellow]")
        sys.exit(0)

    rows = siyuan.find_docs(args.keyword)
    if not rows:
        siyuan.err.print(f"[yellow]没有匹配「{args.keyword}」的文档。[/yellow]")
        sys.exit(0)

    # 只搜不取，或命中多篇 → 列候选
    if args.search or len(rows) > 1:
        print_candidates(rows)
        return

    # 唯一命中
    if args.tree:
        read_tree(resolve_row(rows[0]["id"]))
    else:
        read_one(rows[0]["id"])


if __name__ == "__main__":
    main()
