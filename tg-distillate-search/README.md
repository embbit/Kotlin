# Telegram chat search — import & FTS

Import [Telegram Desktop](https://desktop.telegram.org/) JSON export into SQLite with full-text search.

## Quick start (Mac)

```bash
cd tg-distillate-search

# Import (path to your export folder)
python3 import_export.py ~/Downloads/ChatExport_2026-07-31/result.json -o distillate.db

# Search
python3 search_cli.py дефлегматор
python3 search_cli.py колонна -n 5
```

Import takes a few minutes for ~100k messages. Progress prints every 2000 rows.

## Options

```bash
python3 import_export.py result.json -o distillate.db --username distillate_club_chat --replace
```

| Flag | Description |
|------|-------------|
| `-o` | Output database path (default: `distillate.db`) |
| `--username` | For `t.me/username/msg_id` links |
| `--replace` | Delete existing DB before import |

## Tests

```bash
cd tg-distillate-search
python3 -m unittest discover -s tests -v
```

## Database

- **messages** — id, dates, author, text, reply_to
- **messages_fts** — FTS5 index (unicode61, Russian OK)
- **chat_meta** — chat name, username, import time

## Next steps

1. Copy `distillate.db` to AdminVPS
2. Telegram bot (polling) + same search module
3. Telethon for incremental sync (no weekly export)
