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

# ==================== БАЗА ДАННЫХ ====================
conn = sqlite3.connect('chat_history.db', check_same_thread=False)
cursor = conn.cursor()

# Таблица сообщений
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER,
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        text TEXT,
        file_id TEXT,
        file_type TEXT,
        timestamp TEXT
    )
''')

# Таблица мута
cursor.execute('''
    CREATE TABLE IF NOT EXISTS mutes (
        chat_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY (chat_id, user_id)
    )
''')

# Таблица копирования
cursor.execute('''
    CREATE TABLE IF NOT EXISTS copy (
        chat_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 0
    )
''')

conn.commit()

# ==================== ФУНКЦИИ БАЗЫ ====================

def save_message(msg):
    user = msg.from_user
    file_id = None
    file_type = "text"
    
    if msg.photo:
        file_type = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.voice:
        file_type = "voice"
        file_id = msg.voice.file_id
    elif msg.video:
        file_type = "video"
        file_id = msg.video.file_id
    elif msg.audio:
        file_type = "audio"
        file_id = msg.audio.file_id
    elif msg.document:
        file_type = "document"
        file_id = msg.document.file_id
    elif msg.video_note:
        file_type = "video_note"
        file_id = msg.video_note.file_id
    elif msg.text:
        file_type = "text"
    
    cursor.execute('''
        INSERT OR REPLACE INTO messages (id, chat_id, user_id, username, first_name, text, file_id, file_type, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        msg.message_id,
        msg.chat.id,
        user.id if user else None,
        user.username if user else None,
        user.first_name if user else None,
        msg.text or msg.caption,
        file_id,
        file_type,
        datetime.now().isoformat()
    ))
    conn.commit()

def get_message_by_id(msg_id, chat_id):
    cursor.execute('''
        SELECT first_name, username, text, file_type
        FROM messages
        WHERE id = ? AND chat_id = ?
    ''', (msg_id, chat_id))
    return cursor.fetchone()

def is_muted(chat_id, user_id):
    cursor.execute('SELECT 1 FROM mutes WHERE chat_id=? AND user_id=?', (chat_id, user_id))
    return cursor.fetchone() is not None

def is_copy_enabled(chat_id):
    cursor.execute('SELECT enabled FROM copy WHERE chat_id=?', (chat_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

def get_chat_history(chat_id):
    cursor.execute('''
        SELECT id, first_name, username, text, file_type, timestamp
        FROM messages
        WHERE chat_id = ?
        ORDER BY id
    ''', (chat_id,))
    rows = cursor.fetchall()
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Экспорт чата</title></head>
<body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
    <h1>📦 Экспорт чата</h1>
    <p>Всего сообщений: {len(rows)}</p>
    <hr>
"""
    for row in rows:
        msg_id, name, username, text, file_type, timestamp = row
        user = f"{name} (@{username})" if username else name
        content = text or f"[{file_type}]"
        html += f"""
        <div style="background: white; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 4px solid #0088cc;">
            <strong>{user}</strong> <small style="color: gray;">{timestamp}</small><br>
            {content}
        </div>
        """
    html += "</body></html>"
    return html

async def send_chat_export(chat_id, contact_name=None):
    html = get_chat_history(chat_id)
    name = contact_name or f"chat_{chat_id}"
    filename = f"chat_export_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    with open(filename, "rb") as f:
        await bot.send_document(
            ADMIN_ID,
            f,
            caption=f"📦 Экспорт чата с **{name}**\n\n✅ Контакт удалён."
        )
    
    os.remove(filename)

# ==================== БИЗНЕС-СОБЫТИЯ ====================

@dp.business_connection()
async def business_connect(connection: types.BusinessConnection):
    if connection.is_enabled:
        await bot.send_message(connection.user_id, "✅ Бот подключён к автоматизации чатов!")

@dp.business_message()
async def business_message_handler(message: types.Message):
    if not message.from_user:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем мут
    if is_muted(chat_id, user_id):
        await message.delete()
        await bot.send_message(
            chat_id,
            f"🔇 {message.from_user.first_name}, вы замучены. Сообщение удалено."
        )
        return
    
    # Проверяем копирование
    if is_copy_enabled(chat_id):
        save_message(message)
        logging.info(f"📩 Скопировано: {message.text or message.content_type}")
    else:
        logging.info(f"📩 Сохранено: {message.text or message.content_type}")
        save_message(message)

@dp.edited_business_message()
async def edited_handler(message: types.Message):
    old = get_message_by_id(message.message_id, message.chat.id)
    user = message.from_user
    name = f"{user.first_name} (@{user.username})" if user.username else user.first_name
    
    if old:
        old_text = old[2] or "[медиа]"
        new_text = message.text or "[медиа]"
        await bot.send_message(ADMIN_ID, f"✏️ **{name}** изменил(а) сообщение:\n\n📌 Было: {old_text}\n🆕 Стало: {new_text}")
    else:
        await bot.send_message(ADMIN_ID, f"✏️ **{name}** изменил(а) сообщение (не сохранено)")
    
    save_message(message)

@dp.deleted_business_messages()
async def deleted_handler(deleted: types.BusinessMessagesDeleted):
    for msg_id in deleted.message_ids:
        old = get_message_by_id(msg_id, deleted.chat.id)
        if old:
            name = f"{old[0]} (@{old[1]})" if old[1] else old[0]
            content = old[2] or f"[{old[3]}]"
            await bot.send_message(ADMIN_ID, f"❌ **{name}** удалил(а) сообщение:\n\n{content}")
        else:
            await bot.send_message(ADMIN_ID, f"❌ Удалено сообщение {msg_id} (не сохранено)")
        
        await send_chat_export(deleted.chat.id)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start(message: types.Message):
    webapp_url = "https://basik4z.github.io/daass-site/"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть мини-приложение", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer(
        "✅ **ДААСС активен**\n\n"
        "📌 Команды:\n"
        "• `.mute` — замутить пользователя (ответь на его сообщение)\n"
        "• `.unmute` — размутить\n"
        "• `.copy on` — включить копирование чата\n"
        "• `.copy off` — выключить копирование\n"
        "• `.export` — экспорт чата\n\n"
        "🌐 Открой мини-приложение для полного интерфейса.",
        reply_markup=keyboard
    )

# ==================== МУТ ====================

@dp.message(lambda message: message.text and message.text.startswith('.mute'))
async def mute_user(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя, которого хочешь замутить.")
        return
    
    target = message.reply_to_message.from_user
    chat_id = message.chat.id
    
    cursor.execute('INSERT OR REPLACE INTO mutes (chat_id, user_id) VALUES (?, ?)', (chat_id, target.id))
    conn.commit()
    
    await message.delete()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Размутить", callback_data=f"unmute_{chat_id}_{target.id}")]
    ])
    
    await message.reply_to_message.reply(
        f"🔇 **{target.first_name}** замучен!\n\nСообщения будут удаляться. Нажми кнопку, чтобы размутить.",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text and message.text.startswith('.unmute'))
async def unmute_command(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя, которого хочешь размутить.")
        return
    
    target = message.reply_to_message.from_user
    chat_id = message.chat.id
    
    cursor.execute('DELETE FROM mutes WHERE chat_id=? AND user_id=?', (chat_id, target.id))
    conn.commit()
    
    await message.delete()
    await message.reply_to_message.reply(f"✅ **{target.first_name}** размучен.")

@dp.callback_query(lambda c: c.data and c.data.startswith('unmute_'))
async def unmute_callback(callback: types.CallbackQuery):
    data = callback.data.split('_')
    chat_id = int(data[1])
    user_id = int(data[2])
    
    cursor.execute('DELETE FROM mutes WHERE chat_id=? AND user_id=?', (chat_id, user_id))
    conn.commit()
    
    await callback.message.edit_text(f"✅ Пользователь размучен.")
    await callback.answer()

# ==================== КОПИРОВАНИЕ ====================

@dp.message(lambda message: message.text and message.text.startswith('.copy'))
async def copy_command(message: types.Message):
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("❌ Использование: `.copy on` или `.copy off`")
        return
    
    if args[1].lower() == 'on':
        cursor.execute('INSERT OR REPLACE INTO copy (chat_id, enabled) VALUES (?, ?)', (chat_id, 1))
        conn.commit()
        await message.answer("✅ Копирование чата включено.")
    elif args[1].lower() == 'off':
        cursor.execute('DELETE FROM copy WHERE chat_id=?', (chat_id,))
        conn.commit()
        await message.answer("❌ Копирование чата выключено.")
    else:
        await message.answer("❌ Использование: `.copy on` или `.copy off`")

# ==================== ЭКСПОРТ ====================

@dp.message(Command("export"))
async def export_command(message: types.Message):
    await send_chat_export(message.chat.id)
    await message.answer("📦 Экспорт чата отправлен!")

# ==================== ЗАПУСК ====================

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