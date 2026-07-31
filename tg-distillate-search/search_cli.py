#!/usr/bin/env python3
"""Search imported Telegram chat from the command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tg_search.search import search


def main() -> int:
    parser = argparse.ArgumentParser(description="Search distillate chat database")
    parser.add_argument(
        "query",
        nargs="+",
        help="Search query (words are AND-ed)",
    )
    parser.add_argument(
        "-d",
        "--db",
        type=Path,
        default=Path("distillate.db"),
        help="SQLite database path (default: distillate.db)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Max results (default: 10)",
    )
    args = parser.parse_args()

    if not args.db.is_file():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    q = " ".join(args.query)
    hits = search(args.db, q, limit=args.limit)
    if not hits:
        print("No results.")
        return 0

    for i, hit in enumerate(hits, 1):
        author = hit.from_name or "Unknown"
        print(f"{i}. [{hit.date_iso[:10]}] {author}")
        print(f"   {hit.snippet}")
        print(f"   {hit.link}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
