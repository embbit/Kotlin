# Telegram chat search — import, FTS & bot

Tools for searching the @distillate_club_chat archive.

## 1. Import (Mac)

```bash
cd tg-distillate-search
python3 import_export.py ~/Downloads/ChatExport_2026-07-31/result.json -o distillate.db
python3 search_cli.py дефлегматор
```

## 2. Telegram bot (VPS)

### Create bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → copy token.
2. Learn your Telegram user id ([@userinfobot](https://t.me/userinfobot) or similar).

### Install on VPS

```bash
sudo mkdir -p /opt/distillate
sudo chown $USER:$USER /opt/distillate

# Copy files
scp distillate.db user@vps:/opt/distillate/
scp -r tg-distillate-search user@vps:/opt/distillate/

ssh user@vps
cd /opt/distillate/tg-distillate-search
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example /opt/distillate/.env
nano /opt/distillate/.env   # BOT_TOKEN, ALLOWED_USER_IDS, DB_PATH
```

### Run manually (test)

```bash
cd /opt/distillate/tg-distillate-search
source .venv/bin/activate
set -a && source /opt/distillate/.env && set +a
python bot.py
```

Send a message to the bot in Telegram.

### systemd (24/7)

```bash
sudo cp deploy/distillate-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now distillate-bot
sudo systemctl status distillate-bot
journalctl -u distillate-bot -f
```

Adjust `User=` and paths in the unit file if needed.

## Bot usage

| Input | Action |
|-------|--------|
| `дефлегматор` | Search (up to 5 hits + links) |
| `/start` | Help |
| `/stats` | Archive size, import date |

Only user ids from `ALLOWED_USER_IDS` can use the bot.

## Environment

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | From BotFather |
| `ALLOWED_USER_IDS` | Comma-separated Telegram user ids |
| `DB_PATH` | Path to `distillate.db` |
| `SEARCH_LIMIT` | Results per query (1–10, default 5) |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Roadmap

- [ ] Telethon incremental sync
- [ ] Vector / semantic search
- [ ] Optional LLM summary
