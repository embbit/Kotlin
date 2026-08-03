#!/usr/bin/env python3
"""Telegram bot for full-text search in @distillate_club_chat archive."""

from __future__ import annotations

import logging
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
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
from tg_search.format import FormatResult, _esc, split_hits_to_messages
from tg_search.pagination import (
    clear_sessions,
    get_session,
    keyboard_spec,
    new_session_id,
    next_shown,
    parse_callback,
    save_session,
)
from tg_search.search import search_page
from tg_search.vector_index import VectorIndex, vector_build_stats

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
    "Кнопка <b>Дальше</b> добавляет ещё результаты, <b>Стоп</b> — убирает кнопки.\n"
    "Если не влезает в одно сообщение — продолжение придёт новым.\n"
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


def _search_chunks(
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    shown: int,
) -> tuple[list[FormatResult], bool]:
    config: BotConfig = context.bot_data["config"]
    vector_index = context.bot_data.get("vector_index")
    result = search_page(
        config.db_path,
        query,
        limit=shown,
        offset=0,
        vector_index=vector_index,
    )
    chunks = split_hits_to_messages(result.hits, query)
    has_more = result.has_more and sum(c.fitted for c in chunks) >= shown
    return chunks, has_more


async def _send_html(
    message: Message,
    text: str,
    *,
    reply_markup=None,
    edit: bool = False,
) -> Message:
    kwargs = {
        "text": text,
        "parse_mode": ParseMode.HTML,
        "disable_web_page_preview": True,
        "reply_markup": reply_markup,
    }
    if edit:
        return await message.edit_text(**kwargs)
    return await message.reply_text(**kwargs)


async def _deliver_chunks(
    anchor: Message,
    chunks: list[FormatResult],
    *,
    session_id: str,
    has_more: bool,
    prev_messages: int,
    edit: bool,
) -> None:
    keyboard = _build_keyboard(session_id, has_more=has_more)
    n = len(chunks)

    if n == 1:
        await _send_html(anchor, chunks[0].text, reply_markup=keyboard, edit=edit)
        return

    if n == prev_messages:
        await _send_html(anchor, chunks[-1].text, reply_markup=keyboard, edit=True)
        return

    # Finalize the message that had the button, then send continuation(s).
    await _send_html(anchor, chunks[prev_messages - 1].text, reply_markup=None, edit=True)

    for i in range(prev_messages, n - 1):
        anchor = await _send_html(anchor, chunks[i].text)

    await _send_html(anchor, chunks[-1].text, reply_markup=keyboard)


async def _send_search_page(
    *,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    query: str,
    shown: int,
) -> None:
    chunks, has_more = _search_chunks(context, query, shown)

    if not chunks or chunks[0].fitted == 0:
        text = f"По запросу «{_esc(query)}» ничего не найдено."
        await _send_html(message, text)
        return

    session_id = new_session_id()
    total = sum(c.fitted for c in chunks)
    save_session(
        context.user_data,
        session_id,
        query=query,
        shown=total,
        messages=len(chunks),
    )
    keyboard = _build_keyboard(session_id, has_more=has_more)

    if len(chunks) == 1:
        await _send_html(message, chunks[0].text, reply_markup=keyboard)
        return

    anchor = await _send_html(message, chunks[0].text)
    for chunk in chunks[1:-1]:
        anchor = await _send_html(anchor, chunk.text)
    await _send_html(anchor, chunks[-1].text, reply_markup=keyboard)


def _fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _format_vector_stats(stats: dict) -> str:
    built = int(stats["built"])
    total = int(stats["total"])
    if total <= 0:
        return "нет сообщений в индексе"

    pct = built * 100 // total if total else 0
    nums = f"{_fmt_num(built)} / {_fmt_num(total)}"

    if built >= total:
        status = f"<b>{nums}</b> ({pct}%) — готово"
    elif stats["in_progress"]:
        status = f"<b>{nums}</b> ({pct}%) — <i>идёт построение</i>"
    elif built > 0:
        status = f"<b>{nums}</b> ({pct}%) — не завершено"
    else:
        status = (
            f"<b>0</b> / {_fmt_num(total)} — не построены "
            f"(<code>build_vectors.py</code>)"
        )

    details: list[str] = []
    if stats.get("updated_at") and (stats["in_progress"] or built < total):
        details.append(f"обновлено {_esc(str(stats['updated_at']))}")
    if stats.get("built_at") and built >= total:
        details.append(f"завершено {_esc(str(stats['built_at']))}")
    if stats.get("model") and built > 0:
        details.append(f"модель {_esc(str(stats['model']))}")

    if details:
        return status + "\n  " + ", ".join(details)
    return status


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
        lemmas = get_meta(conn, "lemmas_indexed") or "0"
        sources = list_sources(conn)
        vectors_line = _format_vector_stats(vector_build_stats(conn, message_count=count))
        hrtz = get_meta(conn, "hrtz_article_count") or "0"
        youtube = get_meta(conn, "youtube_video_count") or "0"
        sources_updated = get_meta(conn, "external_sources_updated_at") or "—"
    finally:
        conn.close()

    src_lines = [
        f"• {_esc(s['label'])}: {_esc(s['name'])} (@{_esc(s['username'] or '—')})"
        for s in sources
    ]
    text = (
        f"Сообщений в индексе: <b>{count}</b>\n"
        f"Леммы FTS: <b>{'да' if lemmas == '1' else 'нет — build_lemmas.py'}</b>\n"
        f"Векторы: {vectors_line}\n"
        f"Внешние источники: сайт <b>{hrtz}</b> статей, YouTube <b>{youtube}</b> видео "
        f"(обновлено {_esc(sources_updated)})\n"
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

    await _send_search_page(
        context=context,
        message=update.message,
        query=query,
        shown=config.search_limit,
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BotConfig = context.bot_data["config"]
    callback = update.callback_query
    if not callback or not callback.data or not callback.message:
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
    prev_shown = session["shown"]
    prev_messages = session.get("messages", 1)
    target = next_shown(prev_shown, config.search_limit)
    chunks, has_more = _search_chunks(context, query, target)
    total = sum(c.fitted for c in chunks)

    if total <= prev_shown:
        await callback.edit_message_text(
            f"«{_esc(query)}»\n\nБольше результатов нет.",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    save_session(
        context.user_data,
        session_id,
        query=query,
        shown=total,
        messages=len(chunks),
    )

    await _deliver_chunks(
        callback.message,
        chunks,
        session_id=session_id,
        has_more=has_more,
        prev_messages=prev_messages,
        edit=True,
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
        "Starting bot db=%s allowed_ids=%s allowed_usernames=%s search_limit=%s",
        config.db_path,
        len(config.allowed_user_ids),
        len(config.allowed_usernames),
        config.search_limit,
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
