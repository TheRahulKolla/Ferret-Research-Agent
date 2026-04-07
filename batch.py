"""
Reads topic from topics.txt and runs one agent per topic parllely(upto 10)

"""

import asyncio
import os
from datetime import datetime
from agent import async_run_agent

MAX_CONCURRENT = 10

def read_topics (filepath:str) -> list[str]:
    """
    Read topic from txt file
    """
    with open(filepath, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
    return topics

async def run_batch(topics: list[str]) -> list[dict]: 
    """Run agents for all topics parllely"""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_with_semaphore(topic:str) -> dict :
        async with semaphore:
            print(f"[BATCH] Starting: {topic}")
            result = await async_run_agent(topic)
            print(f"[BATCH] Done: {topic} - status: {result['status']} ({result['duration_sec']}s)")
            return result
    
    tasks = [run_with_semaphore(topic) for topic in topics]
    return await asyncio.gather(*tasks)

def save_batch_summary(results: list[dict]) -> str:
    """ Save summary of all batches to a txt file"""

    os.makedirs("reports", exist_ok= True)
    timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
    filepath = f"reports/batch_summary_{timestamp}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"FERRET BATCH SUMMARY - {timestamp}\n")
        f.write("="*60+ "\n\n")
        for r in results:
            f.write(f"Topic: {r['topic']}\n")
            f.write(f"Status: {r['status']}\n")
            f.write(f"Duration: {r['duration_sec']}\n")
            f.write(f"Iteration: {r['iterations']}\n")
            f.write("-"*40+"\n")

    return filepath

async def main( topics_file: str):
    print(f"reading topics from: {topics_file}")
    topics = read_topics (topics_file)
    print(f"Found {len(topics)} topics. Running batch... \n")

    results = await run_batch(topics)

    summary_path = save_batch_summary(results)
    print(f"\n[BATCH COMPLETE] {len(results)} topics processed.")
    print(f"Summary saved to: {summary_path}")

if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "topics.txt"
    asyncio.run(main(file))