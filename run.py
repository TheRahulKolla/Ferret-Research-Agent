"""
run.py - Entry point for the research agent.

Usage:
    python run.py
    python run.py "Your research topic here"
"""

import sys
import asyncio
from agent import run_agent
from batch import main as batch_main

def main():

    # Batch
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        try:
            topics_file = sys.argv[idx+1]
        except IndexError:
            print("Error: --file requires a filename. Example: python run.py --file topics.txt")
            sys.exit(1)
        asyncio.run(batch_main(topics_file))
        return

    # Single topic from arg
    if len(sys.argv) > 1:
        # Topic passed as command-line argument
        query = " ".join(sys.argv[1:])
    else:
        # Interactive prompt
        print("Research Agent")
        print("-" * 40)
        query = input("Enter research topic: ").strip()
        if not query:
            print("No topic provided. Exiting.")
            sys.exit(1)

    result = run_agent(query)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result.get("report", "No report generated"))
    print(f"\nStatus: {result['status']} | Iterations: {result['iterations']} | Time: {result['duration_sec']}s")


if __name__ == "__main__":
    main()
