#!/usr/bin/env python3
"""
思源笔记结构导出工具（交互式 CLI）

运行前请确认：
  1. 思源笔记已启动（默认端口 6806）
  2. 复制 config.example.json 为 config.json，
     在思源「设置 - 关于」中找到 API Token 并填入

用法示例：
  uv run python main.py                  # 交互式选择笔记本，树状展示
  uv run python main.py --all            # 导出全部笔记本
  uv run python main.py -f json          # 输出 JSON（方便喂给 AI）
  uv run python main.py -a -f markdown -o tree.md
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

import questionary
from questionary import Choice
from rich.console import Console
from rich.tree import Tree

# ── 配置 ──────────────────────────────────────────
# 所有路径都锚定到脚本所在目录，无论从哪里运行都落在项目内
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# 导出文件统一存放的目录
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
# 不指定 -o 时，按格式使用的默认文件名
DEFAULT_NAMES = {"tree": "res.txt", "json": "res.json", "markdown": "res.md"}
# config.json 缺失时的默认值（token 留空，强制用户填写）
DEFAULT_CONFIG = {"url": "http://127.0.0.1:6806", "token": "", "max_depth": 999}
# ─────────────────────────────────────────────────


def load_config() -> dict:
    """从 config.json 读取配置，缺失的字段用 DEFAULT_CONFIG 补齐。

    若文件不存在，提示用户照着 config.example.json 创建。
    """
    if not os.path.exists(CONFIG_PATH):
        err.print("[yellow]⚠ 未找到 config.json[/yellow]")
        err.print("  [dim]请复制 config.example.json 为 config.json，并填入你的 API Token。[/dim]")
        sys.exit(0)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            user_config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        err.print(f"[bold red]✗ 读取 config.json 失败：[/bold red]{e}")
        sys.exit(1)
    return {**DEFAULT_CONFIG, **user_config}

# 数据输出走 stdout，提示信息走 stderr，
# 这样 -f json/markdown 时 stdout 是干净的、可直接管道给 AI。
console = Console()
err = Console(stderr=True)

# 运行时由 main() 从 config.json 填充
SIYUAN_URL = DEFAULT_CONFIG["url"]
API_TOKEN = DEFAULT_CONFIG["token"]
MAX_DEPTH = DEFAULT_CONFIG["max_depth"]


def post(endpoint: str, payload: dict = None) -> dict:
    url = f"{SIYUAN_URL}{endpoint}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Token {API_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        err.print(f"[bold red]✗ 无法连接思源笔记：[/bold red]{e}")
        err.print("  [dim]请确认思源已启动，且地址/端口正确。[/dim]")
        sys.exit(1)

    if result.get("code") != 0:
        err.print(f"[bold red]✗ API 返回异常：[/bold red]{result.get('msg')}")
        sys.exit(1)
    return result["data"]


def get_notebooks() -> list:
    data = post("/api/notebook/lsNotebooks")
    return data.get("notebooks", [])


def get_docs(notebook_id: str, parent_path: str = "/") -> list:
    """通过 SQL 查询某笔记本下某路径的直接子文档"""
    # blocks 表中 type='d' 是文档块，hpath 是可读路径
    # 用 LIKE 匹配直接子级：hpath 匹配 /parent/% 且不含更深的 /
    sql = f"""
        SELECT id, hpath, content
        FROM   blocks
        WHERE  type = 'd'
          AND  box  = '{notebook_id}'
          AND  hpath LIKE '{parent_path.rstrip("/")}/%'
          AND  hpath NOT LIKE '{parent_path.rstrip("/")}/%/%'
        ORDER  BY hpath
    """
    rows = post("/api/query/sql", {"stmt": sql})
    return rows or []


def collect_docs(notebook_id: str, parent_path: str, indent: int) -> list:
    """递归收集某路径下的文档，返回嵌套结构"""
    if indent >= MAX_DEPTH:
        return []
    nodes = []
    for doc in get_docs(notebook_id, parent_path):
        title = doc.get("content") or doc.get("hpath", "").split("/")[-1]
        nodes.append({
            "id": doc["id"],
            "title": title,
            "path": doc["hpath"],
            "children": collect_docs(notebook_id, doc["hpath"], indent + 1),
        })
    return nodes


def collect(notebooks: list) -> dict:
    """把选中的笔记本整理成统一的数据结构"""
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


def render_tree(data: dict, target: Console = None):
    target = target or console
    for nb in data["notebooks"]:
        tree = Tree(f"[bold green]📓 {nb['name']}[/bold green]")
        _add_to_tree(tree, nb["docs"])
        target.print(tree)
        target.print()


def render_tree_text(data: dict) -> str:
    """把彩色树渲染成无颜色的纯文本，供写入 .txt"""
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


# ─────────────────────────────────────────────────

def select_notebooks(notebooks: list) -> list:
    """交互式多选：让用户勾选要导出的笔记本"""
    choices = [
        Choice(title=nb.get("name", nb["id"]), value=nb)
        for nb in notebooks
    ]
    selected = questionary.checkbox(
        "请选择要导出的笔记本（空格勾选，回车确认）：",
        choices=choices,
    ).ask()

    # ask() 在用户按 Ctrl+C 时返回 None
    if selected is None:
        err.print("[yellow]已取消。[/yellow]")
        sys.exit(0)
    return selected


def parse_args():
    parser = argparse.ArgumentParser(
        description="导出思源笔记的文档结构",
    )
    parser.add_argument(
        "-a", "--all", action="store_true",
        help="导出全部笔记本，跳过交互式选择",
    )
    parser.add_argument(
        "-f", "--format", choices=["tree", "json", "markdown"], default="tree",
        help="输出格式：tree（默认彩色树）、json、markdown",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="输出文件名（默认 res.txt/res.json/res.md，均存入 output/）",
    )
    return parser.parse_args()


def main():
    global SIYUAN_URL, API_TOKEN, MAX_DEPTH
    args = parse_args()

    config = load_config()
    SIYUAN_URL = config["url"]
    API_TOKEN = config["token"]
    MAX_DEPTH = config["max_depth"]

    if API_TOKEN in ("", "your_token_here"):
        err.print("[yellow]⚠ 请先在 config.json 填写你的 API Token，然后重新运行。[/yellow]")
        err.print("  [dim]Token 位置：思源笔记 → 设置 → 关于 → API Token[/dim]")
        sys.exit(0)

    err.print("[cyan]正在连接思源笔记……[/cyan]")
    notebooks = [nb for nb in get_notebooks() if not nb.get("closed")]

    if not notebooks:
        err.print("[yellow]未找到任何笔记本（或全部已关闭）。[/yellow]")
        return

    selected = notebooks if args.all else select_notebooks(notebooks)
    if not selected:
        err.print("[yellow]未选择任何笔记本，已退出。[/yellow]")
        return

    data = collect(selected)

    if args.format == "json":
        text = render_json(data)
    elif args.format == "markdown":
        text = render_markdown(data)
    else:  # tree：终端展示彩色版，文件里存纯文本树
        err.print()
        render_tree(data)
        text = render_tree_text(data)

    # 统一落到 OUTPUT_DIR 内；不指定 -o 时用按格式的默认文件名
    filename = os.path.basename(args.output) if args.output else DEFAULT_NAMES[args.format]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    err.print(f"[bold green]✓ 已写入 {path}[/bold green]（共 {len(selected)} 个笔记本）")


if __name__ == "__main__":
    main()
