import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.business_connection()
async def business_connect(connection: types.BusinessConnection):
    if connection.is_enabled:
        await bot.send_message(connection.user_id, "✅ Бот подключён к автоматизации чатов!")

@dp.business_message()
async def business_message_handler(message: types.Message):
    logging.info(f"📩 Сообщение из чата: {message.text}")

@dp.deleted_business_messages()
async def deleted_handler(deleted: types.BusinessMessagesDeleted):
    for msg_id in deleted.message_ids:
        logging.info(f"🗑 Удалено: {msg_id}")
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"❌ Удалено сообщение {msg_id}")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ ДААСС активен. Подключи бота в Настройки → Автоматизация чатов.")

async def main():
    await dp.start_polling(
        bot,
        allowed_updates=[
            "business_connection",
            "business_message",
            "deleted_business_messages",
            "message"
        ]
    )

if __name__ == "__main__":
    asyncio.run(main())