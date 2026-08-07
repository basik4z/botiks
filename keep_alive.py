import os
import sys
import subprocess
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)

def keep_alive():
    """Держит бота живым — перезапускает при падении"""
    logging.info("🔄 Запуск keep_alive...")
    while True:
        try:
            # Пинг Render, чтобы он не усыпил бота
            try:
                requests.get("https://botiks-oqhe.onrender.com")
                logging.info("📡 Пинг успешно отправлен")
            except:
                logging.info("📡 Пинг не удался (но бот работает)")
            
            # Запуск бота
            subprocess.run([sys.executable, "bot.py"])
            
            # Если бот упал — подождать и перезапустить
            logging.warning("⚠️ Бот упал. Перезапуск через 5 секунд...")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.info("🛑 Остановка keep_alive")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")
            time.sleep(10)

if __name__ == "__main__":
    keep_alive()