#!/usr/bin/env python3
"""思源笔记 API 客户端 —— 所有 tools/ 脚本共用的底座。

封装：定位项目根、读取 config.json、POST 调用 kernel API，以及常用的
查询助手（按关键词找文档、列子树、导出 Markdown）。

各工具脚本从项目根用 `uv run python tools/<name>.py` 运行；它们 `import siyuan`
即可拿到这里的 post() / load_config() 等，不要再另起 HTTP 客户端。
"""

import json
import os
import sys
import urllib.error
import urllib.request

from rich.console import Console

# 数据走 stdout（干净、可管道给 AI），提示/日志走 stderr
console = Console()
err = Console(stderr=True)

# 运行时由 init() 从 config.json 填充
SIYUAN_URL = "http://127.0.0.1:6806"
API_TOKEN = ""
MAX_DEPTH = 999

DEFAULT_CONFIG = {"url": "http://127.0.0.1:6806", "token": "", "max_depth": 999}


def find_project_root() -> str:
    """从本文件出发向上找，定位含 pyproject.toml 的项目根。"""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "pyproject.toml")):
            return d
        parent = os.path.dirname(d)
        if parent == d:  # 到根了还没找到，退回脚本上一级
            return os.path.dirname(os.path.abspath(__file__))
        d = parent


PROJECT_ROOT = find_project_root()
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def load_config() -> dict:
    """读取 config.json，缺失字段用默认值补齐；文件不存在则提示并退出。"""
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


def init() -> dict:
    """加载配置并填充模块全局，供 post() 使用。每个工具的入口先调它。"""
    global SIYUAN_URL, API_TOKEN, MAX_DEPTH
    config = load_config()
    SIYUAN_URL = config["url"]
    API_TOKEN = config["token"]
    MAX_DEPTH = config["max_depth"]
    if API_TOKEN in ("", "your_token_here"):
        err.print("[yellow]⚠ 请先在 config.json 填写你的 API Token。[/yellow]")
        err.print("  [dim]Token 位置：思源笔记 → 设置 → 关于 → API Token[/dim]")
        sys.exit(0)
    return config


def post(endpoint: str, payload: dict = None) -> dict:
    """调用思源 kernel API，返回 data 字段；出错时打印并退出。"""
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


def sql(stmt: str) -> list:
    """执行一条 SQL（查 blocks 表），返回行列表。"""
    return post("/api/query/sql", {"stmt": stmt}) or []


def esc(s: str) -> str:
    """转义 SQL 字符串里的单引号。"""
    return s.replace("'", "''")


# ── 常用查询助手 ──────────────────────────────────

def get_notebooks(include_closed: bool = False) -> list:
    data = post("/api/notebook/lsNotebooks")
    nbs = data.get("notebooks", [])
    return nbs if include_closed else [nb for nb in nbs if not nb.get("closed")]


def notebook_names() -> dict:
    """{box_id: name} 映射，供把 box 翻译成笔记本名。"""
    return {nb["id"]: nb.get("name", nb["id"]) for nb in get_notebooks()}


def find_docs(keyword: str, limit: int = 50) -> list:
    """按标题(content)或路径(hpath)模糊找文档块，返回 [{id,hpath,content}]。"""
    kw = esc(keyword)
    return sql(f"""
        SELECT id, hpath, content
        FROM   blocks
        WHERE  type = 'd'
          AND  (content LIKE '%{kw}%' OR hpath LIKE '%{kw}%')
        ORDER  BY hpath
        LIMIT  {limit}
    """)


def descendant_docs(box: str, hpath: str) -> list:
    """某文档子树下的全部后代文档（含各级子文档），按路径排序。"""
    p = esc(hpath.rstrip("/"))
    return sql(f"""
        SELECT id, hpath, content
        FROM   blocks
        WHERE  type = 'd' AND box = '{esc(box)}'
          AND  hpath LIKE '{p}/%'
        ORDER  BY hpath
    """)


def export_markdown(doc_id: str) -> tuple:
    """导出某文档的 Markdown，返回 (hPath, content)。"""
    data = post("/api/export/exportMdContent", {"id": doc_id})
    return data.get("hPath", ""), data.get("content", "")


def doc_title(row: dict) -> str:
    return row.get("content") or row.get("hpath", "").split("/")[-1]


def fmt_ts(ts: str) -> str:
    """思源时间戳 20260613214326 → 2026-06-13 21:43。"""
    if not ts or len(ts) < 12:
        return ts or ""
    return f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}"
