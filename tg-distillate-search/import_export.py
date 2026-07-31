#!/usr/bin/env python3
"""Import Telegram Desktop JSON export into SQLite + FTS5."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tg_search.import_json import import_export


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import Telegram Desktop result.json into SQLite"
    )
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to result.json from Telegram Desktop export",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("distillate.db"),
        help="Output SQLite database path (default: distillate.db)",
    )
    parser.add_argument(
        "--username",
        default="distillate_club_chat",
        help="Public chat username for t.me links (default: distillate_club_chat)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing database before import",
    )
    args = parser.parse_args()

    if not args.json_path.is_file():
        print(f"Error: file not found: {args.json_path}", file=sys.stderr)
        return 1

    print(f"Importing {args.json_path} → {args.output}")
    stats = import_export(
        args.json_path,
        args.output,
        username=args.username,
        replace=args.replace,
    )
    print(
        f"Done: {stats['imported']:,} messages indexed "
        f"({stats['total_in_json']:,} in JSON, "
        f"{stats['skipped']:,} skipped) in {stats['elapsed_sec']}s"
    )
    print(f"Database: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
