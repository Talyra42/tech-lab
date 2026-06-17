#!/usr/bin/env python3
"""最近编辑的文档 —— 回答「我最近在学什么 / 动过哪些笔记」。

按更新时间倒序列出文档。

用法：
  uv run python tools/recent.py              # 最近 20 篇
  uv run python tools/recent.py -l 50        # 最近 50 篇
  uv run python tools/recent.py -n 后端学习   # 限定某笔记本
  uv run python tools/recent.py --created     # 按创建时间排序（看新建了什么）
"""

import argparse

import siyuan


def parse_args():
    parser = argparse.ArgumentParser(description="列出最近编辑的思源文档")
    parser.add_argument("-l", "--limit", type=int, default=20, help="显示条数（默认 20）")
    parser.add_argument("-n", "--notebook", metavar="KEYWORD", help="限定某笔记本（名字关键词）")
    parser.add_argument("--created", action="store_true", help="按创建时间排序（默认按更新时间）")
    return parser.parse_args()


def main():
    args = parse_args()
    siyuan.init()

    names = siyuan.notebook_names()
    box = None
    if args.notebook:
        hit = [b for b, n in names.items() if args.notebook in n]
        if not hit:
            siyuan.err.print(f"[yellow]没有名字含「{args.notebook}」的笔记本。[/yellow]")
            return
        box = hit[0]

    order_col = "created" if args.created else "updated"
    box_cond = f"AND box = '{siyuan.esc(box)}'" if box else ""
    rows = siyuan.sql(f"""
        SELECT id, box, hpath, content, updated, created
        FROM   blocks
        WHERE  type = 'd' {box_cond}
        ORDER  BY {order_col} DESC
        LIMIT  {args.limit}
    """)
    if not rows:
        siyuan.err.print("[yellow]没有找到文档。[/yellow]")
        return

    label = "创建" if args.created else "更新"
    siyuan.err.print(f"[green]最近{label}的 {len(rows)} 篇文档：[/green]\n")
    for r in rows:
        ts = siyuan.fmt_ts(r["created"] if args.created else r["updated"])
        nb = names.get(r["box"], r["box"])
        print(f"{ts}  [{nb}] {r['hpath']}")
        print(f"            id={r['id']}")


if __name__ == "__main__":
    main()
