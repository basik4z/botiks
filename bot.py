import os
import logging
import asyncio
import sqlite3
import random
import re
import time
from datetime import datetime, timedelta
from flask import Flask
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

# ==================== FLASK (для пинга) ====================
app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return "✅ Бот работает"

def run_flask():
    app_flask.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()
logging.info("🌐 Flask-сервер запущен на порту 8080")

# ==================== ОСТАЛЬНОЙ КОД БОТА ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ... (весь остальной код бота, который я давал ранее)

async def main():
    await bot.delete_webhook()
    await dp.start_polling(
        bot,
        allowed_updates=[
            "business_connection",
            "business_message",
            "edited_business_message",
            "deleted_business_messages",
            "message"
        ]
    )

if __name__ == "__main__":
    asyncio.run(main())