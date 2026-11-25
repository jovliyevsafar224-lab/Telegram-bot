from __future__ import annotations

import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from database import Database
from handlers import admin, errors, user
from middlewares import UserMiddleware

logger = logging.getLogger("bot")


def setup_logging() -> None:
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)
    try:
        os.makedirs(settings.log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(settings.log_dir, "bot.log"),
            maxBytes=2_000_000, backupCount=3, encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        logger.warning("Log fayl yaratib bo'lmadi, faqat konsolga yoziladi")


def create_dispatcher(db: Database) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())
    dp.include_router(errors.router)
    dp.include_router(admin.router)  # admin foydalanuvchi router'idan oldin turishi shart
    dp.include_router(user.router)
    return dp


async def on_startup(bot: Bot, db: Database, dispatcher: Dispatcher) -> None:
    await db.connect()
    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s", me.username)

    await bot.set_my_commands(
        [BotCommand(command="start", description="Botni ishga tushirish"),
         BotCommand(command="help", description="Yordam")]
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.set_my_commands(
                [BotCommand(command="start", description="Botni ishga tushirish"),
                 BotCommand(command="help", description="Yordam"),
                 BotCommand(command="admin", description="Admin panel"),
                 BotCommand(command="ban", description="Foydalanuvchini bloklash"),
                 BotCommand(command="unban", description="Blokdan chiqarish")],
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception:
            logger.warning("Admin (%s) uchun buyruqlar o'rnatilmadi (bot hali /start qilinmagan?)", admin_id)

    if settings.use_webhook:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        logger.info("Webhook o'rnatildi: %s", settings.webhook_url)
    else:
        await bot.delete_webhook()
        logger.info("Polling rejimi")


async def on_shutdown(db: Database) -> None:
    await db.close()
    logger.info("Bot to'xtadi")


async def health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


def main() -> None:
    setup_logging()
    if not settings.admin_ids:
        logger.warning("ADMIN_IDS bo'sh — admin panel hech kimga ochiq emas")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    db = Database(settings.db_path)
    dp = create_dispatcher(db)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if settings.use_webhook:
        app = web.Application()
        app.router.add_get("/", health)
        app.router.add_get("/health", health)
        SimpleRequestHandler(
            dispatcher=dp, bot=bot, secret_token=settings.webhook_secret
        ).register(app, path=settings.webhook_path)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=settings.port)
    else:
        asyncio.run(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


if __name__ == "__main__":
    main()
