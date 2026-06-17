#!/usr/bin/env python3
"""全文检索：在所有笔记的「正文」里找关键词，而不只是标题。

回答「我在哪几篇笔记里写过 XXX」。按所属文档归组，给出命中次数、
所在文档路径、文档 ID，以及若干条命中片段。

用法：
  uv run python tools/search.py "goroutine 泄漏"      # 全部笔记本里搜
  uv run python tools/search.py "装饰器" -n 后端学习    # 限定某笔记本
  uv run python tools/search.py "闭包" --snippets 5     # 每篇多看几条片段
  uv run python tools/search.py "Fiber" --docs          # 只列命中的文档，不显片段

拿到文档 ID 后，可用 tools/read.py --id <id> 读全文。
"""

import argparse

import siyuan

# 只在「有正文的叶子块」里搜，避免容器块重复命中
LEAF_TYPES = ("p", "h", "c", "m", "t", "html")


def search_blocks(keyword: str, box: str = None, limit: int = 400) -> list:
    kw = siyuan.esc(keyword)
    types = ",".join(f"'{t}'" for t in LEAF_TYPES)
    box_cond = f"AND box = '{siyuan.esc(box)}'" if box else ""
    return siyuan.sql(f"""
        SELECT id, root_id, box, hpath, content
        FROM   blocks
        WHERE  content LIKE '%{kw}%'
          AND  type IN ({types})
          {box_cond}
        ORDER  BY hpath
        LIMIT  {limit}
    """)


def snippet(text: str, keyword: str, width: int = 50) -> str:
    """截取关键词周围一小段，压平换行。"""
    flat = " ".join(text.split())
    low = flat.lower()
    pos = low.find(keyword.lower())
    if pos < 0:
        return flat[:width * 2]
    start = max(0, pos - width)
    end = min(len(flat), pos + len(keyword) + width)
    s = flat[start:end]
    return ("…" if start > 0 else "") + s + ("…" if end < len(flat) else "")


def parse_args():
    parser = argparse.ArgumentParser(description="思源笔记全文检索")
    parser.add_argument("keyword", help="要搜索的关键词")
    parser.add_argument("-n", "--notebook", metavar="KEYWORD",
                        help="限定某个笔记本（名字关键词）")
    parser.add_argument("--snippets", type=int, default=2,
                        help="每篇文档显示多少条命中片段（默认 2）")
    parser.add_argument("--docs", action="store_true",
                        help="只列命中的文档，不显示片段")
    return parser.parse_args()


def main():
    args = parse_args()
    siyuan.init()

    box = None
    if args.notebook:
        hit = [b for b, n in siyuan.notebook_names().items() if args.notebook in n]
        if not hit:
            siyuan.err.print(f"[yellow]没有名字含「{args.notebook}」的笔记本。[/yellow]")
            return
        box = hit[0]

    rows = search_blocks(args.keyword, box)
    if not rows:
        siyuan.err.print(f"[yellow]没有笔记正文包含「{args.keyword}」。[/yellow]")
        return

    # 按所属文档归组
    docs = {}
    for r in rows:
        d = docs.setdefault(r["root_id"], {"hpath": r["hpath"], "hits": []})
        d["hits"].append(r["content"])

    names = siyuan.notebook_names()
    siyuan.err.print(
        f"[green]「{args.keyword}」命中 {len(rows)} 处，分布在 {len(docs)} 篇笔记：[/green]\n"
    )
    # 命中多的排前面
    for root_id, d in sorted(docs.items(), key=lambda kv: -len(kv[1]["hits"])):
        print(f"● {d['hpath']}")
        print(f"  命中 {len(d['hits'])} 处 · id={root_id}")
        if not args.docs:
            for hit in d["hits"][:args.snippets]:
                print(f"    - {snippet(hit, args.keyword)}")
        print()


if __name__ == "__main__":
    main()
