#!/usr/bin/env python3
"""Build vector embeddings for all messages in the database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tg_search.vector_index import VectorIndex, build_vectors


def main() -> int:
    parser = argparse.ArgumentParser(description="Build vector embeddings for chat search")
    parser.add_argument(
        "-d",
        "--db",
        type=Path,
        default=Path("distillate.db"),
        help="SQLite database path",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Rebuild all vectors from scratch",
    )
    args = parser.parse_args()

    if not args.db.is_file():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    print(f"Building vectors for {args.db} …")
    stats = build_vectors(args.db, replace=args.replace)
    print(
        f"Done: +{stats['built']:,} new, {stats['total_vectors']:,} total, "
        f"model={stats['model']}, {stats.get('elapsed_sec', 0)}s"
    )

    index = VectorIndex.load(args.db)
    if index:
        print(f"Index loaded: {index.count:,} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
