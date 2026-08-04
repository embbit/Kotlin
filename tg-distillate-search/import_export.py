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
        required=True,
        help="Public @username for t.me links (e.g. distillate_club or distillate_club_chat)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Add/update this source in an existing database",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing database before import",
    )
    args = parser.parse_args()

    if args.append and args.replace:
        print("Error: use either --append or --replace, not both", file=sys.stderr)
        return 1

    if not args.json_path.is_file():
        print(f"Error: file not found: {args.json_path}", file=sys.stderr)
        return 1

    print(f"Importing {args.json_path} → {args.output}")
    try:
        stats = import_export(
            args.json_path,
            args.output,
            username=args.username,
            replace=args.replace,
            append=args.append,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Done [{stats['source']}]: +{stats['imported']:,} messages "
        f"({stats['total_in_json']:,} in JSON, {stats['skipped']:,} skipped)"
    )
    print(f"Total in DB: {stats['total_in_db']:,} · {stats['elapsed_sec']}s")
    print(f"Database: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
