import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

# Хранилище статусов (в памяти, для демонстрации)
user_connected = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Проверить подключение", callback_data="check")],
        [InlineKeyboardButton("📊 Статус", callback_data="status")],
        [InlineKeyboardButton("🌐 Сайт", url="https://ggcrachvvv-arch.github.io/Botiks/")]
    ])
    await update.message.reply_text(
        "🤖 **ДААСС — твой помощник в Telegram**\n\n"
        "✅ Бот активен\n"
        "📌 Нажми кнопку, чтобы проверить подключение к чатам.",
        reply_markup=keyboard
    )

async def check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    msg = await query.edit_message_text("🔄 Проверка подключения...")

    for i in range(1, 11):
        percent = i * 10
        squares = "🟩" * i + "⬜" * (10 - i)
        await msg.edit_text(f"📡 Проверка: {percent}%\n{squares}")
        import asyncio
        await asyncio.sleep(0.3)

    if user_connected.get(user_id, False):
        await msg.edit_text("✅ **ДААСС активирован!**\n\nБот видит твои чаты.")
    else:
        await msg.edit_text(
            "❌ **ДААСС не подключён к чатам!**\n\n"
            "📌 Проверь:\n"
            "1️⃣ Есть ли Telegram Premium?\n"
            "2️⃣ Бот добавлен в Настройки → Автоматизация чатов?\n"
            "3️⃣ Ты написал кому-нибудь сообщение ПОСЛЕ добавления?\n\n"
            "🔄 После выполнения условий нажми кнопку снова.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check")]
            ])
        )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📊 **Статус ДААСС**\n\n"
        "🟢 Бот: активен\n"
        "🔄 Режим: long polling\n"
        "📦 Сообщений в памяти: 0\n"
        "👤 Пользователей: 0\n\n"
        "⚠️ Для отслеживания удалений нужен Telegram Premium и Business API."
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'/start'), start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="check"))
    app.add_handler(CallbackQueryHandler(status_callback, pattern="status"))
    logging.info("ДААСС запущен")
    app.run_polling()

if __name__ == "__main__":
    main()