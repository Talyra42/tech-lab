---
name: siyuan-read
description: Read, search, and analyze the user's local SiYuan (思源笔记) notebooks. Use whenever the user asks you to read, summarize, explain, search, compare, or check progress on their SiYuan notes — SiYuan stores notes in its own block format, not plain Markdown, so the only way in is the SiYuan kernel API via the tools/ scripts here.
---

# 读取与分析思源笔记（SiYuan）

思源的内容不是普通 Markdown 文件，无法直接 `Read`，必须走思源 kernel API。
本仓库在 `tools/` 下封装好了一组脚本，全部从**项目根目录**用 `uv run` 运行，
数据输出走 stdout（可直接读），提示信息走 stderr。

前提：思源客户端正在运行（默认 `http://127.0.0.1:6806`），`config.json` 填了 API Token
（脚本自动读取，已 gitignore）。若没读到内容，先确认思源是否开着。

## 工具一览

### 看结构 — `tools/structure.py`
```bash
uv run python tools/structure.py -f markdown        # 全部笔记本，Markdown（最适合阅读）
uv run python tools/structure.py -f json            # JSON
uv run python tools/structure.py -n 后端学习         # 只看名字含「后端学习」的笔记本
```

### 读正文 — `tools/read.py`
```bash
uv run python tools/read.py "React Fiber"           # 关键词查找并输出正文
uv run python tools/read.py --id <文档ID>           # 按 ID 精确读
uv run python tools/read.py -s "Fiber"              # 只列候选，不输出正文
uv run python tools/read.py --id <ID> --tree        # 整个主题：该文档 + 全部子文档
```
- 唯一命中 → 直接输出 Markdown（首行 `<!-- hPath -->` 标路径）
- 命中多篇 → 列候选（序号/标题/路径/id），挑出后用 `--id` 再读
- 整章/整个主题总结时用 `--tree`，一次拿全

### 全文检索 — `tools/search.py`
搜笔记**正文**而非标题，回答「我在哪几篇里写过 XXX」：
```bash
uv run python tools/search.py "goroutine 泄漏"       # 全库搜
uv run python tools/search.py "装饰器" -n 后端学习     # 限定笔记本
uv run python tools/search.py "闭包" --docs           # 只列命中文档，不显片段
```
结果按文档归组，给出命中次数 + 路径 + id + 片段；拿 id 去 `read.py --id` 读全文。

### 最近编辑 — `tools/recent.py`
回答「我最近在学什么 / 动过哪些笔记」：
```bash
uv run python tools/recent.py                       # 最近 20 篇（按更新时间）
uv run python tools/recent.py -l 50 -n 后端学习       # 某笔记本最近 50 篇
uv run python tools/recent.py --created             # 按创建时间（看新建了啥）
```

### 体量统计 — `tools/stats.py`
```bash
uv run python tools/stats.py                        # 各笔记本文档数/字数一览
```

## 典型流程

- 「读一下 React Fiber 那篇」→ `read.py "React Fiber"` → 多候选则按路径选对的 → `read.py --id <id>`
- 「总结一下我的 Ink 学习」→ `structure.py -n` 或 `read.py --id <Ink父文档> --tree` 拿全部正文再总结
- 「我哪儿写过闭包陷阱」→ `search.py "闭包陷阱"`
- 「我最近在学什么」→ `recent.py`

## 需要别的能力时（扩展）

完整 API 文档已下载到本仓库：
- 中文：[docs/siyuan-api_zh_CN.md](../../../docs/siyuan-api_zh_CN.md)
- 英文：[docs/siyuan-api.md](../../../docs/siyuan-api.md)

常用端点：`/api/notebook/lsNotebooks`（列笔记本）、`/api/query/sql`（查 blocks 表，`type='d'` 是文档块、
`hpath` 是可读路径、`root_id` 是所属文档、`updated`/`created` 是时间戳）、
`/api/export/exportMdContent`（`{id}`→导出 Markdown）、`/api/filetree/getIDsByHPath`（路径反查 ID）。

新增能力时，在 `tools/` 下加脚本并 `import siyuan` 复用 `post()` / `load_config()` / 查询助手，
不要另起 HTTP 客户端。删文件要先经用户同意。
