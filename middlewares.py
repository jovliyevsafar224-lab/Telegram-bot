from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings
from database import Database


class UserMiddleware(BaseMiddleware):
    """Har bir xabar/callback'da foydalanuvchini bazaga yozadi va bloklanganlarni to'xtatadi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        db: Database = data["db"]
        if user is None or user.is_bot:
            return await handler(event, data)

        is_new, banned = await db.touch_user(user)
        if banned and user.id not in settings.admin_ids:
            if isinstance(event, CallbackQuery):
                await event.answer("🚫 Siz bloklangansiz.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("🚫 Siz bloklangansiz.")
            return None
        data["is_new_user"] = is_new
        return await handler(event, data)
