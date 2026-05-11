# AI News Summarizer

AI News Summarizer 是一个轻量级的个人新闻智能看板。它从 RSS、网页、API 或本地文件抓取内容，然后通过 CLI 和 FastAPI Web 界面进行摘要展示。

默认配置将 `AIHot` 设为最高优先级源。该源已经过 LLM 筛选和摘要，因此应用会直接复用其内容和评分，避免重复调用 LLM。

## 功能特性

- 多源接入：RSS、网页爬虫、API、本地文件
- 多 LLM 提供商支持：OpenAI 兼容 API、Anthropic、Ollama
- AIHot 优先级排序和评分提取
- 本地历史缓存，刷新页面无需重新抓取 RSS
- 历史搜索 API 和 Web 端搜索面板
- CLI 和 FastAPI Web 双入口

## 环境要求

- Python 3.11+
- `uv`
- 如需对非预摘要源进行摘要，需要配置 LLM API Key

## 安装

```powershell
uv sync --dev
Copy-Item .env.example .env
```

编辑 `.env` 填入你的 API Key：

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

`config/default_config.yaml` 中默认使用 MiniMax 作为 OpenAI 兼容提供商：

```yaml
llm:
  default: "openai"
  providers:
    openai:
      model: "MiniMax-M2.7"
      base_url: "https://api.minimax.chat/v1"
```

## 本地运行

Web 界面：

```powershell
uv run uvicorn ai_news_summarizer.web.app:app --host 127.0.0.1 --port 8000
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

CLI：

```powershell
uv run ai-news summarize -c ./config/default_config.yaml
```

## 历史缓存

每次成功运行会自动保存到：

```text
data/history.json
```

该文件已被 Git 忽略。Web 页面加载时会调用：

```text
GET /api/history/latest
```

刷新页面可直接恢复上次结果，无需重新抓取。搜索接口：

```text
GET /api/history/search?q=关键词
```

## Docker 部署

构建镜像：

```powershell
docker build -t ai-news-summarizer .
```

运行容器：

```powershell
docker run --rm -p 8000:8000 --env-file .env -v ${PWD}/data:/app/data ai-news-summarizer
```

然后访问：

```text
http://127.0.0.1:8000
```

## 配置说明

数据源在 `config/default_config.yaml` 中配置。

高优先级预摘要源示例：

```yaml
sources:
  - type: "rss"
    name: "aihot_virxact"
    params:
      url: "https://aihot.virxact.com/feed.xml"
      max_items: 20
      priority: 100
      pre_summarized: true
```

条目按源优先级排序，再按提取的推荐评分排序。

## 安全提醒

以下文件不要提交到 Git：

- `.env`（API Key）
- `.venv/`（虚拟环境）
- `.uv-cache/`（缓存）
- `data/history.json`（运行时数据）
- `results.html`（生成的报告）

项目的 `.gitignore` 已默认排除这些文件。

## 项目文档

- `docs/maintenance-log.md` — 重要变更记录
- `docs/project-health.md` — 已知问题和待办事项
