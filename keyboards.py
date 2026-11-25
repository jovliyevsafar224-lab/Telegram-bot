from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Bot haqida", callback_data="menu:about")
    kb.button(text="👤 Profilim", callback_data="menu:profile")
    kb.button(text="❓ Yordam", callback_data="menu:help")
    if is_admin:
        kb.button(text="🛠 Admin panel", callback_data="admin:panel")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Asosiy menyu", callback_data="menu:main")
    return kb.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="admin:stats")
    kb.button(text="👥 Foydalanuvchilar", callback_data="admin:users")
    kb.button(text="📣 Xabar yuborish", callback_data="admin:broadcast")
    kb.button(text="🐞 Xatolar", callback_data="admin:errors")
    kb.button(text="📥 CSV eksport", callback_data="admin:export")
    kb.button(text="⬅️ Asosiy menyu", callback_data="menu:main")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


def back_to_admin() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Admin panel", callback_data="admin:panel")
    return kb.as_markup()


def broadcast_confirm() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yuborish", callback_data="admin:send")
    kb.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    kb.adjust(2)
    return kb.as_markup()


def cancel_only() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    return kb.as_markup()
