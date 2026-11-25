# Telegram bot (aiogram 3) — admin panel, baza, Render deploy

## Imkoniyatlar
- `/start`, `/help`, inline tugmali menyu (Bot haqida, Profilim, Yordam)
- Admin panel (`/admin`): statistika, foydalanuvchilar, ommaviy xabar, xatolar, CSV eksport, `/ban`, `/unban`
- SQLite baza (foydalanuvchilar + xatolar jadvali)
- Xatolar: konsol + `logs/bot.log` (aylanuvchi) + bazaga + adminlarga xabar
- Token faqat Environment Variables orqali

## 1. Tayyorgarlik
1. Telegramda **@BotFather** → `/newbot` → **token** oling.
2. O'z Telegram ID'ngizni **@userinfobot** orqali bilib oling (bu `ADMIN_IDS`).

## 2. Lokal ishga tushirish
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # BOT_TOKEN va ADMIN_IDS ni to'ldiring
python main.py
```
Lokal rejimda bot avtomatik **polling** bilan ishlaydi.

## 3. Render'ga deploy
1. Loyihani GitHub'ga yuklang (`.env` yuklanmaydi — `.gitignore` da).
2. Render → **New → Blueprint** → repozitoriyni tanlang (`render.yaml` avtomatik o'qiladi).
3. So'ralganda kiriting: `BOT_TOKEN`, `ADMIN_IDS` (bir nechta bo'lsa vergul bilan).
4. Deploy tugagach loglarda `Webhook o'rnatildi` va `Bot ishga tushdi` yozuvi chiqadi.
5. Botga `/start` yozing, so'ng `/admin`.

Render `RENDER_EXTERNAL_URL` ni o'zi beradi — bot shu orqali **webhook** rejimiga o'tadi.

### Muhim eslatmalar
- **Baza saqlanishi:** SQLite fayl bo'lgani uchun Renderda doimiy **Disk** kerak (`render.yaml` da `/var/data`, pullik reja). Bepul rejada har deploy/restartda baza o'chadi — katta loyiha uchun Render PostgreSQL ga o'tish tavsiya etiladi.
- **Bepul reja uyquga ketadi:** ~15 daqiqa so'rov bo'lmasa servis uxlaydi, birinchi xabar kechikadi.
- **Token sizib ketsa:** @BotFather → `/revoke`, Renderda `BOT_TOKEN` ni yangilang.

## Tuzilma
```
main.py            ishga tushirish (webhook/polling), logging
config.py          Environment Variables
database.py        SQLite
keyboards.py       inline tugmalar
middlewares.py     foydalanuvchini yozish, ban tekshiruvi
handlers/          user.py, admin.py, errors.py, utils.py
render.yaml        Render konfiguratsiyasi
```
