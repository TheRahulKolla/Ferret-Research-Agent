"""
Reads topics and runs one agent per topic in parallel (up to MAX_CONCURRENT).
Supports output_format (docx/txt) and auto-retries each failed topic once.
"""

import asyncio
import os
import queue
from datetime import datetime
from agent import async_run_agent

MAX_CONCURRENT = 10

# Global queue for SSE events
sse_queue = queue.Queue()


def emit(event: str, topic: str, data: dict = {}):
    """Push a status event into the SSE queue."""
    sse_queue.put({"event": event, "topic": topic, "data": data})


def read_topics(filepath: str) -> list[str]:
    """Read topics from a txt file."""
    with open(filepath, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
    return topics


async def run_batch(topics: list[str], output_format: str = "docx") -> list[dict]:
    """Run agents for all topics in parallel with auto-retry on failure."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_once(topic: str) -> dict:
        """Run the agent for a single topic (no retry logic here)."""
        def progress_callback(iteration, max_iterations):
            pct = round((iteration / max_iterations) * 100)
            emit("progress", topic, {
                "iteration": iteration,
                "max_iterations": max_iterations,
                "pct": pct
            })

        return await async_run_agent(topic, progress_callback=progress_callback, output_format=output_format)

    async def run_with_semaphore(topic: str) -> dict:
        async with semaphore:
            emit("started", topic)
            print(f"[BATCH] Starting: {topic}")

            try:
                result = await run_once(topic)

                # Auto-retry once if first attempt failed
                if result.get("status") != "success":
                    print(f"[BATCH] Retrying: {topic}")
                    emit("retrying", topic, {"reason": result.get("status", "failed")})
                    result = await run_once(topic)

                if result.get("status") == "success":
                    emit("done", topic, {
                        "status": result["status"],
                        "duration_sec": result["duration_sec"],
                        "iterations": result["iterations"]
                    })
                    print(f"[BATCH] Done: {topic} ({result['duration_sec']}s)")
                else:
                    emit("failed", topic, {"error": result.get("status", "unknown error")})
                    print(f"[BATCH] Failed after retry: {topic}")

                return result

            except Exception as e:
                # Auto-retry once on exception
                print(f"[BATCH] Exception, retrying: {topic} — {e}")
                emit("retrying", topic, {"reason": str(e)})
                try:
                    result = await run_once(topic)
                    emit("done", topic, {
                        "status": result["status"],
                        "duration_sec": result["duration_sec"],
                        "iterations": result["iterations"]
                    })
                    return result
                except Exception as e2:
                    emit("failed", topic, {"error": str(e2)})
                    print(f"[BATCH] Failed after retry: {topic} — {e2}")
                    return {
                        "topic": topic,
                        "status": "failed",
                        "report": "",
                        "iterations": 0,
                        "duration_sec": 0
                    }

    tasks = [run_with_semaphore(topic) for topic in topics]
    return await asyncio.gather(*tasks)


def save_batch_summary(results: list[dict]) -> str:
    """Save a summary of all batch results to a txt file."""
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
    filepath = f"reports/batch_summary_{timestamp}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"FERRET BATCH SUMMARY - {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        for r in results:
            f.write(f"Topic: {r['topic']}\n")
            f.write(f"Status: {r['status']}\n")
            f.write(f"Duration: {r['duration_sec']}s\n")
            f.write(f"Iterations: {r['iterations']}\n")
            f.write("-" * 40 + "\n")

    return filepath


async def main(topics_file: str):
    print(f"Reading topics from: {topics_file}")
    topics = read_topics(topics_file)
    print(f"Found {len(topics)} topics. Running batch...\n")

    results = await run_batch(topics)

    summary_path = save_batch_summary(results)
    print(f"\n[BATCH COMPLETE] {len(results)} topics processed.")
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "topics.txt"
    asyncio.run(main(file))
