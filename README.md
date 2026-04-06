# Ferret Research Agent

An autonomous AI research agent that searches the web, synthesizes information, and saves structured reports — all from a single command.

## How it works

Uses the **ReAct loop** (Reason → Act → Observe → repeat):
1. You give it a research topic
2. It breaks it into focused search queries
3. Searches the web using DuckDuckGo
4. Synthesizes results into a structured report
5. Saves the report with sources to the `reports/` folder

## Project Structure

```
├── agent.py      # ReAct loop — sends messages to Claude
├── tools.py      # Tools: web_search, save_report, read_file
├── run.py        # Entry point — takes user input
├── reports/      # Saved research reports (auto-created)
└── .env          # API key (not committed)
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

```bash
# Interactive mode
python run.py

# Pass topic directly
python run.py "future of artificial intelligence"
```

## Tech Stack

- [Claude Haiku](https://anthropic.com) — AI brain via Anthropic API
- [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) — free web search, no API key needed
- Python 3.10+
