#!/usr/bin/env python3
"""Backfill lemmatized text and rebuild lemma-aware FTS index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tg_search.lemmas import build_lemmas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build lemmatized FTS index for an existing database"
    )
    parser.add_argument(
        "-d",
        "--db",
        type=Path,
        default=Path("distillate.db"),
        help="SQLite database path (default: distillate.db)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows per update batch (default: 500)",
    )
    args = parser.parse_args()

    if not args.db.is_file():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    print(f"Building lemmas for {args.db} ...")
    stats = build_lemmas(args.db, batch_size=args.batch_size)
    print(
        f"Done: updated {stats['updated']:,} rows in {stats['elapsed_sec']}s "
        f"(FTS now uses lemmas)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
