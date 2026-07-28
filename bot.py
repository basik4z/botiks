import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

user_connected = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 Проверить подключение", callback_data="check")]]
    await update.message.reply_text(
        "🔐 **ДААСС**\n\nНажми кнопку, чтобы проверить подключение.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    msg = await query.edit_message_text("🔄 Проверка...")

    for i in range(1, 11):
        percent = i * 10
        squares = "🟩" * i + "⬜" * (10 - i)
        await msg.edit_text(f"📡 {percent}%\n{squares}")

    if user_connected.get(user_id, False):
        await msg.edit_text("✅ **ДААСС активирован!**")
    else:
        await msg.edit_text(
            "❌ **ДААСС не подключён!**\n\n"
            "1️⃣ Premium?\n"
            "2️⃣ Автоматизация чатов?\n"
            "3️⃣ Сообщение после добавления?\n\n"
            "🔄 Нажми снова.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Проверить снова", callback_data="check")]])
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r'/start'), start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="check"))
    app.run_polling()

if __name__ == "__main__":
    main()