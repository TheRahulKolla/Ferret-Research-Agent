"""
agent.py - The brain of our research agent.

Implements the ReAct loop:
  Reason → Act (tool call) → Observe (tool result) → Reason again → ...
  Until Claude decides it has a final answer.
"""

import os
import json
import asyncio
import time
import anthropic
from dotenv import load_dotenv
from tools import CORE_TOOL_DEFINITIONS, TOOL_DEFINITIONS, execute_tool
from prompts import SYSTEM_PROMPT, DECOMPOSITION_PROMPT
load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Haiku - fastest and cheapest Claude model
MODEL = "claude-haiku-4-5-20251001"

def query_planner (topic:str) -> list[str]:
    """
    Use claude to decompose a topic into 2-3 sub-queries. """

    print(f"planning queries for: {topic}")
    response = client.messages.create(
        model= MODEL,
        max_tokens=512,
        messages = [{
            "role":"user",
            "content":DECOMPOSITION_PROMPT.format(topic=topic)
        }]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]
    text = text.strip()
    queries = json.loads(text)
    print(f"Sub-queries: {queries}")
    return queries

def trim_history(messages: list, keep_last: int = 10) -> list:
    """FIX 1: Keep first message (the enriched query) + last N to prevent context bloat."""
    if len(messages) <= keep_last + 1:
        return messages
    return [messages[0]] + messages[-(keep_last):]


def run_agent(user_query: str, max_iterations: int = 10, progress_callback=None) -> dict:
    """
    Run the ReAct agent loop.

    Args:
        user_query: The research topic from the user
        max_iterations: Safety limit to prevent infinite loops

    Returns:
        dict with keys: topic, status, report, iterations, duration_sec
    """
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"AGENT STARTING: {user_query}")
    print(f"{'='*60}\n")

    #Plan sub-queries first
    sub_queries = query_planner(user_query)
    combined = "\n".join(f"- {q}" for q in sub_queries)
    # FIX 6: removed duplicate raw topic — sub-queries already cover it
    enriched_query = f"Please search and answer these sub-queries:\n{combined}"

    messages = [
        {"role": "user", "content": enriched_query}
    ]

    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")

        # FIX 3: dynamic max_tokens — 512 for tool calls, 4096 only for final response
        is_last_iteration = (iteration == max_iterations)
        dynamic_max_tokens = 4096 if is_last_iteration else 512

        trimmed = trim_history(messages)  # FIX 1: trim context before each call

        response = client.messages.create(
            model=MODEL,
            max_tokens=dynamic_max_tokens,
            system=SYSTEM_PROMPT,
            tools=CORE_TOOL_DEFINITIONS,  # FIX 5: send core tools only
            messages=trimmed
        )

        print(f"Stop reason: {response.stop_reason}")

        # sync trimmed back so next iteration appends to the trimmed version
        messages = list(trimmed)

        # --- CASE 1: Claude is done, no more tool calls ---
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            print(f"\nAGENT DONE after {iteration} iterations.")
            return {
                "topic": user_query,
                "status": "success",
                "report": final_text,
                "iterations": iteration,
                "duration_sec": round(time.time() - start_time, 2)
            }

        # --- CASE 2: Claude wants to use a tool ---
        if response.stop_reason == "tool_use":

            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    print(f"  Tool called: {tool_name}")
                    print(f"  Input: {tool_input}")

                    result = execute_tool(tool_name, tool_input)

                    print(f"  Result preview: {result[:150]}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Emit progress after each tool use iteration
            if progress_callback:
                progress_callback(iteration, max_iterations)

        else:
            print(f"Unexpected stop reason: {response.stop_reason}")
            break

    return {
        "topic": user_query,
        "status": "max_iterations_reached",
        "report": "",
        "iterations": max_iterations,
        "duration_sec": round(time.time() - start_time, 2)
    }

async def async_run_agent(user_query: str, max_iterations: int = 10, progress_callback=None) -> dict:
    """Async wrapper for run_agent — runs in thread pool to avoid blocking."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_agent, user_query, max_iterations, progress_callback)
