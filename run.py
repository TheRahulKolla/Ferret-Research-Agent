"""
run.py - Entry point for the research agent.

Usage:
    python run.py
    python run.py "Your research topic here"
"""

import sys
from agent import run_agent


def main():
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
    print(result)


if __name__ == "__main__":
    main()
