# siyuan-copilot

这是一个 **AI 笔记副驾仓库**：用户不在这里手写代码，仓库纯粹用来「和 AI 讨论思源笔记」。
里面放的是给你（Claude）用的工具脚本和 API 文档——你来运行脚本读取笔记内容，然后陪用户讨论。

思源笔记（SiYuan）把内容存成自有的块格式、**不是普通 Markdown**，无法用 `Read` 直接打开，
一切内容都要走思源 kernel API（脚本已封装好）。

## 怎么读用户的思源笔记

当用户让你读 / 总结 / 检索 / 对比 / 分析他的思源笔记时，使用 **siyuan-read** Skill
（`.claude/skills/siyuan-read/SKILL.md`，里面有每个工具的详细用法）。

工具都在 `tools/`，从项目根用 `uv run` 跑，输出走 stdout（可直接读）：

| 想做的事 | 命令 |
|---|---|
| 看结构（有哪些笔记本/文档） | `uv run python tools/structure.py -f markdown` |
| 读某篇正文 | `uv run python tools/read.py "关键词"` → 多个候选再 `--id <id>` |
| 读整个主题（含子文档） | `uv run python tools/read.py --id <id> --tree` |
| 全文搜内容（不只标题） | `uv run python tools/search.py "关键词"` |
| 最近编辑了啥 | `uv run python tools/recent.py` |
| 各笔记本体量统计 | `uv run python tools/stats.py` |

前提：思源客户端在运行，且 `config.json` 填了 API Token。

## 项目结构

- `tools/` — 给 AI 运行的工具脚本
  - [tools/siyuan.py](tools/siyuan.py) — 共享 API 客户端：`post()` / `load_config()` / 查询助手，**新增能力时复用它**
  - [tools/structure.py](tools/structure.py) — 导出笔记本结构（树 / JSON / Markdown）
  - [tools/read.py](tools/read.py) — 读单篇或整个子树的 Markdown 正文
  - [tools/search.py](tools/search.py) — 全文检索笔记正文
  - [tools/recent.py](tools/recent.py) — 最近编辑的文档
  - [tools/stats.py](tools/stats.py) — 各笔记本文档数/字数统计
- `config.json` — URL / Token / 深度（gitignore，本地私有）；`config.example.json` 是提交进仓库的模板
- `output/` — 结构导出文件（gitignore）
- [docs/siyuan-api_zh_CN.md](docs/siyuan-api_zh_CN.md) — 思源完整 API 文档（扩展能力时查这里）

## 约定

- 新增思源相关能力时，在 `tools/` 下加脚本并 `import siyuan` 复用 `post()` / `load_config()`，不要另起 HTTP 客户端。
- 配置（URL / Token / max_depth）只放 `config.json`，不要再硬编码进代码。
- 脚本一律从项目根目录用 `uv run python tools/<name>.py` 运行（依赖和 venv 都在根目录）。
- 删除文件需先经用户同意；新增工具/功能可自行进行。
