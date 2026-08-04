"""Bot access control: search whitelist and admin commands."""

from __future__ import annotations

from tg_search.config import BotConfig


def user_in_list(
    user,
    *,
    user_ids: frozenset[int],
    usernames: frozenset[str],
) -> bool:
    if user is None:
        return False
    if user.id in user_ids:
        return True
    username = (user.username or "").lower()
    return bool(username) and username in usernames


def allowed_user(config: BotConfig, user) -> bool:
    return user_in_list(
        user,
        user_ids=config.allowed_user_ids,
        usernames=config.allowed_usernames,
    )


def admin_user(config: BotConfig, user) -> bool:
    return user_in_list(
        user,
        user_ids=config.admin_user_ids,
        usernames=config.admin_usernames,
    )
