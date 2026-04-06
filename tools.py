"""
3 tools the agent can use:
    1. web_search - DuckDuckGo
    2. save_report - saves to local
    3. read_file - reads saved files
"""

import os
from datetime import datetime
from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
        if not results:
            return "No results found."
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"[{i}] {r['title']}\n{r['snippet']}\nSource: {r['url']}")
        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search error: {str(e)}"


def save_report(filename: str, content: str) -> str:
    """Save a report to reports/ folder."""
    try:
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = filename.replace(" ", "_").replace("/", "-")
        filepath = f"reports/{safe_name}_{timestamp}.txt"
        
        structured = f"""
========================================================================
FERRET RESEARCH REPORT
========================================================================
Generated: {datetime.now().strftime("%m-%d-%Y %H:%M:%S")}
Topic: {filename}
========================================================================

{content}

========================================================================
END OF REPORT
========================================================================
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(structured)
        return f"Report saved to: {filepath}"
    except Exception as e:
        return f"Save error: {str(e)}"


def read_file(filepath: str) -> str:
    """Read a saved file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"
    except Exception as e:
        return f"Read error: {str(e)}"

def merge_results (results: list) -> str:
    """Merge multiple search result block into one formatted string"""
    merged= []
    for i, result in enumerate(results, 1):
        merged.append(f"=== Search Result Block{i} === \n{result}")
    return "\n\n".join(merged)
   
TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Search the web for up-to-date information. Use when you need facts or data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_report",
        "description": "Save the final report to a local file when research is complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Report filename (no extension)"},
                "content": {"type": "string", "description": "Full report content"}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read content of a previously saved report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file"}
            },
            "required": ["filepath"]
        }
    },
    {
        "name":"merge_results",
        "description": "Merge multiple search result blocks into one formatted block before writing the report.",
        "input_schema":{
            "type":"object",
            "properties": {
                "results": {"type": "array", "items": {"type":"string"}, "description": "List of search strings to merge"}
            },
            "required":["results"]
        }
    }
]

TOOL_MAP = {
    "web_search": web_search,
    "save_report": save_report,
    "read_file": read_file,
    "merge_results": merge_results
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name not in TOOL_MAP:
        return f"Unknown tool: {tool_name}"
    return TOOL_MAP[tool_name](**tool_input)
