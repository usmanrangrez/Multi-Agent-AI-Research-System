# 🔬 Multi-Agent AI Researcher

Ask a research question. A team of four AI agents searches the web, reads the sources, writes a report, and reviews it before you see it. If the reviewer rejects a draft, the writer revises it. A Streamlit UI shows the whole pipeline live.

Built with **Python · LangChain · Gemini · Tavily · Streamlit**.

---

## How it works

```
Question
   │
   ▼
🔎 Search Agent ──► finds sources via Tavily
   │
   ▼
📖 Reader Agent ──► opens each page, extracts what matters for the question
   │
   ▼
✍️ Writer Agent ──► drafts a structured report from the findings only
   │
   ▼
🧐 Critic Agent ──► approves, or returns concrete feedback
   │        │
   │        └── rejected ──► Writer revises ──► Critic reviews again (up to N rounds)
   ▼
📄 Final report + sources
```

| Agent | Job | Tools |
|---|---|---|
| Search | Finds relevant web sources | `search_web` (Tavily) |
| Reader | Reads one page, extracts relevant facts | `read_webpage` (requests + BeautifulSoup) |
| Writer | Synthesizes findings into a report; never invents facts | none |
| Critic | Checks the draft against the findings, returns structured `approved` + `feedback` | none (Pydantic `CriticResult`) |

The Python code in `workflow/research.py` orchestrates the agents explicitly, so data flows Search → Reader → Writer → Critic in a fixed, inspectable order.

## Features

- **Live pipeline view:** step states, durations, a read counter (3/5), a time-share chart and a color-coded event log
- **Critic revision loop** with a configurable number of rounds
- **Strict critic mode:** requires source citations, a Sources section and a Limitations section, so you can watch real rejections and revisions
- **Resilient runs:** retries on transient API or network errors, skips unreadable pages, and falls back to calling the search tool directly if the model skips it
- **Sources tab:** every source link plus what the Reader extracted from it
- **Downloads:** report as `.md` or `.txt`, with a sources list
- **History:** reopen earlier runs in the same session
- **Clear errors:** readable messages with hints and an expandable traceback

## Project structure

```
.
├── app.py                  # Streamlit UI
├── workflow/
│   └── research.py         # pipeline orchestration, events, retries
├── agents/
│   ├── search.py           # search agent
│   ├── reader.py           # reader agent
│   ├── writer.py           # writer agent + prompt builder
│   └── critic.py           # critic agent (structured output)
├── tools/
│   ├── search.py           # Tavily search tool
│   └── web_reader.py       # webpage fetch + text extraction tool
├── schemas/
│   └── critic.py           # CriticResult (approved, feedback)
├── pyproject.toml
├── uv.lock
└── Dockerfile
```

## Getting started

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini)
- A [Tavily](https://tavily.com/) API key

### Install

```bash
git clone https://github.com/usmanrangrez/Multi-Agent-AI-Research-System
cd —
uv sync
```

### Configure

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your-gemini-key
TAVILY_API_KEY=your-tavily-key
```

`.env` is gitignored. Never commit it.

### Run the app

```bash
uv run streamlit run app.py
```

Open http://localhost:8501, type a question (or click an example) and press **Start Research**.

### Run without the UI

```bash
uv run python -m workflow.research
```

This prints every pipeline event and the final report to the terminal.

## Settings

| Setting | Where | What it does |
|---|---|---|
| Max critic rounds | Sidebar slider | How many times the Critic can review. More rounds mean more time and tokens |
| Strict critic | Sidebar toggle | Critic approves only if every claim cites its source and Sources and Limitations sections exist |

## Deployment

### Docker (works on Render, Railway, Fly.io, Hugging Face Spaces, any VPS)

```bash
docker build -t researcher .
docker run -p 8501:8501 \
  -e GOOGLE_API_KEY=your-gemini-key \
  -e TAVILY_API_KEY=your-tavily-key \
  researcher
```

**Render:** New → Web Service → connect the GitHub repo → runtime **Docker** → add the two environment variables → deploy.

**Streamlit Community Cloud:** deploy `app.py`, commit `uv.lock`, and add both keys under **Secrets**.

> The app has no login. Anyone with the URL can use your API quota, so keep it private or add a password gate before sharing it publicly.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `Server disconnected` / `RemoteProtocolError` | Transient Gemini error. The app retries automatically. If it persists, cap page text in `tools/web_reader.py` |
| Search agent skipped the tool | Handled: the pipeline calls `search_web` directly as a fallback |
| 401 / API key errors | Check `GOOGLE_API_KEY` and `TAVILY_API_KEY` |
| 429 / quota errors | Free-tier limit hit, wait a minute and retry |
| `No module named agents` | Add empty `__init__.py` files to `agents/`, `tools/`, `workflow/`, `schemas/` |
| Every source failed to load | Some sites block scrapers, retry or rephrase the question |

## Known limitations

- Answers are only as good as the pages the Reader can fetch; JavaScript-heavy sites may return little text.
- The Critic checks the report against the collected findings, not against the live web, so it cannot catch errors the sources themselves contain.
- Sessions and history live in memory and reset when the app restarts.

## License

MIT, or choose your own.
