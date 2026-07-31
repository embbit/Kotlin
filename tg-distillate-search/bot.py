#!/usr/bin/env python3
"""Telegram bot for full-text search in @distillate_club_chat archive."""

from __future__ import annotations

import logging
import sys

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from tg_search.config import BotConfig
from tg_search.db import connect, get_meta
from tg_search.format import _esc, format_hits
from tg_search.search import search

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("distillate-bot")

HELP_TEXT = (
    "Поиск по архиву чата <b>Дистиллят &amp; Чат</b>.\n\n"
    "Отправьте слова запроса — верну до 5 сообщений со ссылками.\n"
    "Несколько слов = все должны встретиться (AND).\n\n"
    "Команды:\n"
    "/start — эта справка\n"
    "/stats — сведения об архиве"
)


def _allowed(config: BotConfig, user_id: int | None) -> bool:
    return user_id is not None and user_id in config.allowed_user_ids


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.effective_user or not _allowed(config, update.effective_user.id):
        await update.message.reply_text("Доступ запрещён.")
        return
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.effective_user or not _allowed(config, update.effective_user.id):
        await update.message.reply_text("Доступ запрещён.")
        return

    conn = connect(config.db_path)
    try:
        count = get_meta(conn, "message_count") or "?"
        chat_name = get_meta(conn, "chat_name") or "?"
        imported = get_meta(conn, "imported_at") or "?"
    finally:
        conn.close()

    text = (
        f"<b>{_esc(chat_name)}</b>\n"
        f"Сообщений в индексе: <b>{count}</b>\n"
        f"Импорт: {_esc(imported)}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.message or not update.effective_user:
        return
    if not _allowed(config, update.effective_user.id):
        await update.message.reply_text("Доступ запрещён.")
        return

    query = (update.message.text or "").strip()
    if not query:
        return
    if query.startswith("/"):
        return

    await update.message.chat.send_action("typing")
    hits = search(config.db_path, query, limit=config.search_limit)
    text = format_hits(hits, query)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def main() -> int:
    try:
        config = BotConfig.from_env()
    except RuntimeError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    if not config.db_path.is_file():
        print(f"Database not found: {config.db_path}", file=sys.stderr)
        return 1

    log.info(
        "Starting bot db=%s allowed_users=%s",
        config.db_path,
        len(config.allowed_user_ids),
    )

    app = Application.builder().token(config.token).build()
    app.bot_data["config"] = config
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
