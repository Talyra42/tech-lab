#!/usr/bin/env python3
"""笔记本统计 —— 各笔记本的文档数 / 内容字数概览，给出学习体量的鸟瞰。

用法：
  uv run python tools/stats.py            # 所有笔记本一览
  uv run python tools/stats.py --json     # JSON 输出
"""

import argparse
import json

import siyuan

# 统计字数时只数有正文的叶子块，避免容器块重复计入
LEAF_TYPES = ("p", "h", "c", "m", "t", "html")


def gather() -> list:
    names = siyuan.notebook_names()
    types = ",".join(f"'{t}'" for t in LEAF_TYPES)

    doc_rows = siyuan.sql("SELECT box, COUNT(*) AS n FROM blocks WHERE type='d' GROUP BY box")
    docs = {r["box"]: int(r["n"]) for r in doc_rows}

    char_rows = siyuan.sql(f"""
        SELECT box, SUM(LENGTH(content)) AS chars
        FROM   blocks
        WHERE  type IN ({types})
        GROUP  BY box
    """)
    chars = {r["box"]: int(r["chars"] or 0) for r in char_rows}

    stats = []
    for box, name in names.items():
        stats.append({
            "notebook": name,
            "docs": docs.get(box, 0),
            "chars": chars.get(box, 0),
        })
    stats.sort(key=lambda s: -s["chars"])
    return stats


def parse_args():
    parser = argparse.ArgumentParser(description="思源笔记本统计")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    return parser.parse_args()


def main():
    args = parse_args()
    siyuan.init()
    stats = gather()

    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    total_docs = sum(s["docs"] for s in stats)
    total_chars = sum(s["chars"] for s in stats)
    siyuan.err.print(f"[green]共 {len(stats)} 个笔记本 · {total_docs} 篇文档 · 约 {total_chars:,} 字[/green]\n")
    print(f"{'笔记本':<16}{'文档数':>8}{'约字数':>12}")
    print("─" * 40)
    for s in stats:
        print(f"{s['notebook']:<16}{s['docs']:>8}{s['chars']:>12,}")


if __name__ == "__main__":
    main()
