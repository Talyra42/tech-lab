# siyuan-copilot

你思源笔记的 **AI 副驾**：不在这里手写代码，而是用来「和 AI 讨论我的思源笔记」。

思源笔记把内容存成自有的块格式、不是普通 Markdown，AI 无法直接打开。本仓库在 `tools/`
下封装了一组调用思源 kernel API 的脚本，**由 AI（Claude Code）运行**来读取、检索、分析笔记，
然后陪你讨论、总结、查漏补缺。你只管开着思源、提问就行。

## 怎么用

在本项目里直接跟 Claude Code 说人话，例如：

- 「读一下 React Fiber 那篇，帮我总结」
- 「我哪几篇笔记写过闭包陷阱？」
- 「我最近在学什么？」
- 「我的 Ink 学到哪了，还差啥？」

Claude 会自动用 `siyuan-read` Skill 调下面的工具，先取内容再帮你处理。
**唯一前提：思源客户端开着**（API 才通）。

## 环境要求

- Python ≥ 3.11、[uv](https://docs.astral.sh/uv/)
- 思源笔记已启动（默认端口 `6806`）

## 配置

复制模板并填入 Token（Token 位置：思源笔记 → 设置 → 关于 → API Token）：

```bash
cp config.example.json config.json
# 编辑 config.json，填入 token
```

`config.json` 已被 `.gitignore` 忽略，不会提交。

## 工具（由 AI 运行，也可手动跑）

全部从项目根用 `uv run python tools/<name>.py` 运行：

| 脚本 | 作用 |
|------|------|
| `tools/structure.py` | 导出笔记本结构（树 / JSON / Markdown） |
| `tools/read.py` | 读单篇或整个子树（`--tree`）的 Markdown 正文 |
| `tools/search.py` | 全文检索笔记正文（不只标题） |
| `tools/recent.py` | 列出最近编辑的文档 |
| `tools/stats.py` | 各笔记本文档数 / 字数统计 |

每个脚本都有 `-h` 帮助。`tools/siyuan.py` 是它们共用的 API 客户端。

## 项目结构

```
.claude/skills/siyuan-read/   # 教 AI 怎么用这些工具的 Skill
tools/                        # API 工具脚本
docs/                         # 思源完整 API 文档（扩展功能时查）
config.json                   # URL / Token / 深度（私有，gitignore）
config.example.json           # 配置模板
output/                       # 结构导出文件（gitignore）
```

## 工作原理

通过思源本地 HTTP API：`/api/notebook/lsNotebooks` 列笔记本、`/api/query/sql` 查 `blocks`
表（文档块 `type='d'`）、`/api/export/exportMdContent` 把文档导出为 Markdown。完整 API
见 [docs/siyuan-api_zh_CN.md](docs/siyuan-api_zh_CN.md)。
