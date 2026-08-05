"""Telegram bot command menu and group mention parsing."""

from __future__ import annotations

from telegram import Bot, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeDefault
from telegram.constants import MessageEntityType
from telegram import Message


async def register_bot_commands(bot: Bot) -> None:
    """Register command hints for private chats and groups."""
    private_commands = [
        BotCommand("start", "Справка по боту"),
        BotCommand("help", "Справка по боту"),
        BotCommand("search", "Поиск: /search слова запроса"),
        BotCommand("stats", "Сведения об архиве (админ)"),
        BotCommand("search_stats", "Статистика поисков (админ)"),
    ]
    group_commands = [
        BotCommand("start", "Справка по боту"),
        BotCommand("help", "Справка по боту"),
        BotCommand("search", "Поиск: /search слова запроса"),
    ]
    await bot.set_my_commands(private_commands, scope=BotCommandScopeDefault())
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())


def query_from_mention(message: Message, bot_username: str) -> str | None:
    """Extract search query from «@bot слова» in a group message."""
    text = (message.text or "").strip()
    if not text or not bot_username:
        return None

    tag = f"@{bot_username}".lower()
    entities = message.entities or []
    for entity in entities:
        if entity.type != MessageEntityType.MENTION:
            continue
        mention = text[entity.offset : entity.offset + entity.length]
        if mention.lower() != tag:
            continue
        before = text[: entity.offset].strip()
        after = text[entity.offset + entity.length :].strip()
        query = " ".join(part for part in (before, after) if part).strip()
        return query or None
    return None
