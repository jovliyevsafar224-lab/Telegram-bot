"""Sozlamalar faqat Environment Variables orqali o'qiladi (token kodda yo'q)."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # lokal ishlatish uchun .env faylini o'qiydi (Renderda kerak emas)


def _parse_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            raise RuntimeError(f"ADMIN_IDS ichida noto'g'ri qiymat: {part!r}") from None
    return frozenset(ids)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    db_path: str
    log_dir: str
    port: int
    base_url: str  # bo'sh bo'lsa polling, aks holda webhook
    webhook_path: str = "/webhook"

    @property
    def use_webhook(self) -> bool:
        return bool(self.base_url)

    @property
    def webhook_url(self) -> str:
        return f"{self.base_url}{self.webhook_path}"

    @property
    def webhook_secret(self) -> str:
        # Tokendan hosil qilinadi: alohida sir saqlash shart emas
        return hashlib.sha256(f"wh:{self.bot_token}".encode()).hexdigest()[:48]


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. Uni Environment Variables (yoki lokal .env) orqali bering."
        )
    base = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
    return Settings(
        bot_token=token,
        admin_ids=_parse_ids(os.getenv("ADMIN_IDS", "")),
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        log_dir=os.getenv("LOG_DIR", "logs"),
        port=int(os.getenv("PORT", "10000")),
        base_url=base,
    )


settings = load_settings()
