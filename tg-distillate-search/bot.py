#!/usr/bin/env python3
"""Telegram bot for full-text search in @distillate_club_chat archive."""

from __future__ import annotations

import logging
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from tg_search.config import BotConfig
from tg_search.db import connect, count_messages, get_meta, list_sources
from tg_search.format import _esc, format_hits
from tg_search.pagination import (
    clear_sessions,
    get_session,
    keyboard_spec,
    new_session_id,
    parse_callback,
    save_session,
)
from tg_search.search import search_page
from tg_search.vector_index import VectorIndex

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("distillate-bot")


def _build_keyboard(session_id: str, *, has_more: bool) -> InlineKeyboardMarkup | None:
    spec = keyboard_spec(session_id, has_more=has_more)
    if spec is None:
        return None
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(label, callback_data=data) for label, data in row]
            for row in spec
        ]
    )


HELP_TEXT = (
    "Поиск по архиву <b>Дистиллят</b> (канал + чат).\n\n"
    "Отправьте слова запроса — верну первые результаты со ссылками.\n"
    "Кнопки <b>Дальше</b> / <b>Стоп</b> — листать дальше или закрыть.\n"
    "Приоритет у <b>свежих</b> сообщений.\n\n"
    "Команды:\n"
    "/start — справка\n"
    "/stats — сведения об архиве"
)


def _allowed(config: BotConfig, user) -> bool:
    if user is None:
        return False
    if user.id in config.allowed_user_ids:
        return True
    username = (user.username or "").lower()
    return bool(username) and username in config.allowed_usernames


async def _deny_access(update: Update) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id is not None:
        await update.message.reply_text(
            f"Доступ запрещён.\nВаш Telegram id: <code>{user_id}</code>\n"
            "Передайте его администратору для whitelist.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text("Доступ запрещён.")


async def _deny_callback(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer("Доступ запрещён.", show_alert=True)


def _run_search(context: ContextTypes.DEFAULT_TYPE, query: str, offset: int):
    config: BotConfig = context.bot_data["config"]
    vector_index = context.bot_data.get("vector_index")
    page_size = config.search_limit
    result = search_page(
        config.db_path,
        query,
        limit=page_size,
        offset=offset,
        vector_index=vector_index,
    )
    page_num = offset // page_size + 1
    start_index = offset + 1
    text = format_hits(
        result.hits,
        query,
        start_index=start_index,
        page=page_num,
    )
    return result, text, page_num, page_size


async def _send_search_page(
    *,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    query: str,
    offset: int,
    reply_fn,
    edit_message=None,
) -> None:
    result, text, page_num, page_size = _run_search(context, query, offset)

    if not result.hits:
        if offset > 0:
            text = f"«{_esc(query)}»\n\nБольше результатов нет."
        await reply_fn(text, reply_markup=None)
        return

    session_id = new_session_id()
    save_session(
        context.user_data,
        session_id,
        query=query,
        offset=offset + len(result.hits),
    )
    keyboard = _build_keyboard(session_id, has_more=result.has_more)

    await reply_fn(text, reply_markup=keyboard)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.effective_user or not _allowed(config, update.effective_user):
        await _deny_access(update)
        return
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.effective_user or not _allowed(config, update.effective_user):
        await _deny_access(update)
        return

    conn = connect(config.db_path)
    try:
        count = count_messages(conn)
        imported = get_meta(conn, "imported_at") or "?"
        vectors = get_meta(conn, "vector_count") or "0"
        sources = list_sources(conn)
    finally:
        conn.close()

    src_lines = [
        f"• {_esc(s['label'])}: {_esc(s['name'])} (@{_esc(s['username'] or '—')})"
        for s in sources
    ]
    text = (
        f"Сообщений в индексе: <b>{count}</b>\n"
        f"Векторов: <b>{vectors}</b>\n"
        f"Источники:\n" + "\n".join(src_lines) + "\n"
        f"Импорт: {_esc(imported)}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    if not update.message or not update.effective_user:
        return
    if not _allowed(config, update.effective_user):
        await _deny_access(update)
        return

    query = (update.message.text or "").strip()
    if not query or query.startswith("/"):
        return

    clear_sessions(context.user_data)
    await update.message.chat.send_action("typing")

    async def reply(text, reply_markup=None):
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    await _send_search_page(
        context=context,
        chat_id=update.message.chat_id,
        query=query,
        offset=0,
        reply_fn=reply,
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    callback = update.callback_query
    if not callback or not callback.data:
        return

    if not update.effective_user or not _allowed(config, update.effective_user):
        await _deny_callback(update)
        return

    parsed = parse_callback(callback.data)
    if not parsed:
        await callback.answer()
        return

    action, session_id = parsed
    session = get_session(context.user_data, session_id)
    if not session:
        await callback.answer("Сессия устарела — отправьте запрос заново.", show_alert=True)
        return

    query = session["query"]

    if action == "stop":
        await callback.answer("Остановлено")
        try:
            await callback.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        sessions = context.user_data.get("search_sessions", {})
        sessions.pop(session_id, None)
        return

    await callback.answer()
    offset = session["offset"]
    result, text, _, _ = _run_search(context, query, offset)

    if not result.hits:
        await callback.edit_message_text(
            f"«{_esc(query)}»\n\nБольше результатов нет.",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    new_offset = offset + len(result.hits)
    save_session(
        context.user_data,
        session_id,
        query=query,
        offset=new_offset,
    )
    page_num = offset // config.search_limit + 1
    text = format_hits(
        result.hits,
        query,
        start_index=offset + 1,
        page=page_num,
    )
    keyboard = _build_keyboard(session_id, has_more=result.has_more)

    await callback.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=keyboard,
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
        "Starting bot db=%s allowed_ids=%s allowed_usernames=%s",
        config.db_path,
        len(config.allowed_user_ids),
        len(config.allowed_usernames),
    )

    vector_index = VectorIndex.load(config.db_path)
    if vector_index:
        log.info("Vector index loaded: %s embeddings", vector_index.count)
    else:
        log.warning("Vector index missing — run build_vectors.py (FTS + recency only)")

    app = Application.builder().token(config.token).build()
    app.bot_data["config"] = config
    app.bot_data["vector_index"] = vector_index
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
