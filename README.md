# Ferret Research Agent

An autonomous AI research agent that searches the web, synthesizes information, and saves structured `.docx` reports — with a clean web UI for drag-drop batch uploads and live progress tracking.

## How it works

Uses the **ReAct loop** (Reason → Act → Observe → repeat):
1. You give it a research topic
2. It decomposes it into 2-3 focused sub-queries
3. Searches the web for each sub-query
4. Synthesizes results into a structured report with sections and sources
5. Saves the report as a `.docx` Word file to the `reports/` folder

## Project Structure

```
├── agent.py           # ReAct loop — async-safe, returns structured dict
├── tools.py           # Tools: web_search, docx_writer, read_file, merge_results
├── prompts.py         # System prompt and query decomposition prompt
├── batch.py           # Batch mode — runs multiple topics in parallel with SSE events
├── app.py             # Flask web UI — upload, progress, reports routes
├── run.py             # CLI entry point — single topic or batch mode
├── topics.txt         # Sample topics file for batch mode
├── templates/
│   └── index.html     # Single-page web UI
├── static/
│   ├── style.css      # Flat design system (Inter, blue/gray palette)
│   └── app.js         # Drag-drop, SSE listener, live progress, preview modal
├── reports/           # Saved research reports (auto-created)
└── .env               # API key (not committed)
```

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

**4. Add your API key**

Create a `.env` file in the root directory:
```
ANTHROPIC_API_KEY=your-api-key-here
```
Get your key at [console.anthropic.com](https://console.anthropic.com)

## Usage

### Web UI (recommended)
```bash
python app.py
# Open http://localhost:5000
```

- **Upload** — type a single topic or drag-drop a `topics.txt` for batch
- **Progress** — watch live per-topic progress bars update every iteration
- **Reports** — download or preview any `.docx` report inline

### CLI
```bash
# Interactive mode
python run.py

# Single topic
python run.py "future of artificial intelligence"

# Batch mode — research multiple topics in parallel
python run.py --file topics.txt
```

### topics.txt format
One topic per line (max 10):
```
Future of quantum computing
Impact of climate change on agriculture
Rise of electric vehicles
```

## Tech Stack

- [Claude Haiku](https://anthropic.com) — AI brain via Anthropic API
- [DuckDuckGo Search](https://pypi.org/project/ddgs/) — free web search, no API key needed
- [python-docx](https://python-docx.readthedocs.io/) — `.docx` report generation
- [Flask](https://flask.palletsprojects.com/) — web UI and SSE streaming
- Python 3.10+
