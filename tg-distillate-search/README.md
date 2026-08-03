# Telegram chat search — import, FTS & bot

Tools for searching the @distillate_club_chat archive.

## 1. Import (Mac)

**Чат** (уже есть) + **канал** @distillate_club — два отдельных экспорта из Telegram Desktop.

```bash
cd tg-distillate-search

# Первый источник (чат) — полная база
python3 import_export.py ~/Downloads/ChatExport_.../result.json \
  -o distillate.db --username distillate_club_chat --replace

# Канал — добавить в ту же базу
python3 import_export.py ~/Downloads/ChannelExport_.../result.json \
  -o distillate.db --username distillate_club --append

# Пересобрать векторы для новых постов канала
python3 build_vectors.py -d distillate.db

python3 search_cli.py дефлегматор
```

| Флаг | Значение |
|------|----------|
| `--username` | @username для ссылок (`distillate_club` или `distillate_club_chat`) |
| `--replace` | Удалить базу и импортировать заново (только первый раз) |
| `--append` | Добавить/обновить источник в существующую базу |

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

### Update code on VPS

**На VPS** (если новый код ещё не залит):

```bash
# одноразово — скачать скрипт и обновить
curl -fsSL https://raw.githubusercontent.com/embbit/Kotlin/cursor/tg-distillate-import-e619/tg-distillate-search/deploy/update-vps.sh \
  | bash
```

Или вручную:

```bash
cd /tmp
git clone -b cursor/tg-distillate-import-e619 --depth 1 https://github.com/embbit/Kotlin.git
rsync -av --exclude '.venv' --exclude '__pycache__' --exclude '*.db' --exclude '.env' \
  Kotlin/tg-distillate-search/ /opt/distillate/tg-distillate-search/
systemctl restart distillate-bot
```

**С Mac** (когда код уже есть локально):

```bash
cd tg-distillate-search
./deploy/deploy.sh root@89.125.75.11
```

## 3. Build lemmas (word forms in FTS)

For an **existing** database, run once after deploy:

```bash
pip install -r requirements.txt
systemctl stop distillate-bot
python3 build_lemmas.py -d /opt/distillate/distillate.db
systemctl restart distillate-bot
```

~103k messages: a few minutes on CPU. New imports lemmatize automatically.

Search then matches word forms: `сухопарник` finds `сухопарника`, `сухопарники`, etc.

## 4. Build vectors (semantic + fresh results)

```bash
pip install -r requirements.txt
systemctl stop distillate-bot
python3 build_vectors.py -d /opt/distillate/distillate.db
systemctl restart distillate-bot
```

First run downloads embedding model (~100MB). ~105k messages: 30–90 min on CPU.

Search = **lemmatized FTS + vectors + recency** (newer messages rank higher).

## 5. External sources (hrtz.store + YouTube)

Articles from **https://hrtz.store/** (`/page*.html` from sitemap) and videos from **@DistillateClub** are indexed into the same database and appear in mixed search results with labels `[сайт]` and `[youtube]`.

```bash
# one-shot sync (FTS + incremental vectors for new chunks)
python3 update_sources.py -d /opt/distillate/distillate.db

# web or YouTube only
python3 update_sources.py -d distillate.db --web-only
python3 update_sources.py -d distillate.db --youtube-only
```

**Cron (daily 04:00 UTC)** on VPS:

```bash
sudo cp deploy/distillate-sources.cron /etc/cron.d/distillate-sources
```

Log: `/opt/distillate/update_sources.log`

Telegram vectors are **not** rebuilt — only new/changed external chunks are embedded.

## Bot usage

| Input | Action |
|-------|--------|
| `дефлегматор` | Search (first page + links, recent first) |
| **Дальше ➡️** / **Стоп** | Добавить ещё результаты / убрать кнопки (при переполнении — новое сообщение) |
| `/start` | Help |
| `/stats` | Archive size, lemmas, **vector build progress** (N / total), import date |

Only users from `ALLOWED_USERNAMES` / `ALLOWED_USER_IDS` can use the bot.

Default usernames in `.env.example`: `embbit`, `Kir_UA6CT`, `m_hrtz`. On VPS edit `/opt/distillate/.env` and restart the bot.

## Environment

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | From BotFather |
| `ALLOWED_USER_IDS` | Comma-separated Telegram user ids (optional) |
| `ALLOWED_USERNAMES` | Comma-separated usernames without @ (optional) |
| `DB_PATH` | Path to `distillate.db` |
| `SEARCH_LIMIT` | Results per query (1–10, default 5) |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Roadmap

- [ ] Telethon incremental sync
- [x] Vector / semantic search + recency
- [ ] Optional LLM summary
