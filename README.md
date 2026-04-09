# Ferret Research Agent

An autonomous AI research agent that searches the web, synthesizes information, and produces structured reports — with a full web UI featuring live progress tracking, batch processing, export options, and error recovery.

---

## What makes Ferret unique

- **Fully autonomous ReAct loop** — Ferret reasons, searches, observes results, and iterates without any human intervention until the report is done
- **Live progress bars via SSE** — every iteration update streams to the browser in real time using Server-Sent Events, no polling
- **Batch + parallel execution** — research up to 10 topics simultaneously using `asyncio` + semaphore concurrency
- **Auto-retry on failure** — each failed topic is automatically retried once before being marked as failed
- **Export format choice** — output as `.docx` (Word) or `.txt` per run, toggled from the UI
- **Download all as .zip** — one click zips every report and downloads it
- **Query decomposition** — Claude automatically breaks any topic into 2–3 focused sub-queries for deeper coverage
- **Dark / light mode** — theme persists across sessions via localStorage
- **Settings UI** — API keys, agent config (iterations, concurrency, sub-queries), and danger zone all managed from the browser
- **Token-efficient design** — trimmed message history, truncated search snippets, dynamic max_tokens, and core-only tool schemas reduce costs significantly

---

## How it works

Ferret uses the **ReAct loop** (Reason → Act → Observe → repeat):

1. You provide a research topic (single or batch)
2. Claude decomposes it into 2–3 focused sub-queries
3. Ferret searches the web for each sub-query
4. Results are synthesized into a structured report (Overview, Key Findings, Details, Sources)
5. The report is saved as `.docx` or `.txt` to the `reports/` folder
6. Live progress is streamed to your browser via SSE throughout

---

## Project Structure

```
├── agent.py           # ReAct loop — query planner, run_agent, async wrapper
├── tools.py           # Tools: web_search, docx_writer, txt_writer, read_file, merge_results
├── prompts.py         # SYSTEM_PROMPT and DECOMPOSITION_PROMPT
├── batch.py           # Batch runner — parallel execution, SSE events, auto-retry
├── app.py             # Flask web server — all routes and API endpoints
├── run.py             # CLI entry point — single topic or batch mode
├── topics.txt         # Sample topics file for batch mode
├── templates/
│   └── index.html     # Single-page web UI (4 screens)
├── static/
│   ├── style.css      # Full design system — light/dark theme, animations
│   └── app.js         # UI logic — drag-drop, SSE listener, progress, modals
├── reports/           # Saved research reports (auto-created)
└── .env               # API keys (not committed)
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/TheRahulKolla/Ferret-Research-Agent.git
cd Ferret-Research-Agent
```

**2. Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API keys**

Create a `.env` file in the root directory:
```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
```

- Anthropic key: [console.anthropic.com](https://console.anthropic.com)
- Tavily key: [tavily.com](https://tavily.com) (free tier available)

Or add them directly from the Settings screen in the web UI.

---

## Usage

### Web UI (recommended)
```bash
python app.py
# Open http://localhost:5000
```

**Upload screen**
- Type a single topic and click Run, or switch to Batch mode
- Drag and drop a `topics.txt` file (one topic per line, up to 10)
- Choose output format: `.docx` or `.txt`

**Progress screen**
- Live per-topic progress bars updated every agent iteration via SSE
- Status chips: queued → running → done / failed
- Failure log displayed after batch completes for any failed topics

**Reports screen**
- View all saved reports with format indicator
- Preview any report inline (modal)
- Download individual reports or all as a single `.zip`

**Settings screen**
- Save Anthropic and Tavily API keys (validated, stored in `.env`)
- Tune agent behaviour: max sub-queries, max iterations, max concurrent topics
- Clear all reports from the danger zone

### CLI
```bash
# Interactive mode
python run.py

# Single topic
python run.py "future of artificial intelligence"

# Batch mode
python run.py --file topics.txt
```

### topics.txt format
One topic per line (max 10):
```
Future of quantum computing
Impact of climate change on agriculture
Rise of electric vehicles
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Web UI |
| POST | `/upload` | Upload topics, start batch (accepts `format=docx\|txt`) |
| GET | `/status` | SSE stream of live progress events |
| GET | `/reports` | List all saved reports |
| GET | `/download/<file>` | Download a single report |
| GET | `/download-all` | Download all reports as `.zip` |
| GET | `/preview/<file>` | Preview report content as plain text |
| POST | `/save-key` | Save API key to `.env` |
| POST | `/save-config` | Save agent config to `.env` |
| GET | `/get-settings` | Fetch current settings |
| POST | `/clear-reports` | Delete all reports |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| AI brain | [Claude Haiku](https://anthropic.com) via Anthropic API |
| Web search | [Tavily](https://tavily.com) |
| Report generation | [python-docx](https://python-docx.readthedocs.io/) |
| Web framework | [Flask](https://flask.palletsprojects.com/) |
| Live streaming | Server-Sent Events (SSE) |
| Concurrency | Python asyncio + semaphore |
| Frontend | Vanilla JS, CSS custom properties |

---

## MVP History

| MVP | Branch | What was built |
|-----|--------|----------------|
| MVP 1 | `mvp-1` | Core ReAct loop, DuckDuckGo search, txt report output |
| MVP 2 | `mvp-2` | Query decomposition, structured reports, GitHub setup |
| MVP 3 | `mvp-3` | Batch processing, async parallel execution, .docx export |
| MVP 4 | `mvp-4` | Flask web UI, SSE live progress, drag-drop upload, dark mode, settings screen |
| MVP 3a | `mvp-3a` | Tavily search, token optimizations (trim history, dynamic max_tokens, snippet truncation) |
| MVP 5 | `mvp-4` | .docx/.txt toggle, txt_writer, auto-retry, failure log, download-all .zip |
