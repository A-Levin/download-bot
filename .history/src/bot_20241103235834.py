import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils import executor
from yt_dlp import YoutubeDL
import os

API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Лимит на размер файла в байтах (50 MB для всех ботов в Telegram)
TELEGRAM_FILE_SIZE_LIMIT = 50 * 1024 * 1024

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.reply("Привет! Я бот для загрузки контента с YouTube. Отправь ссылку на видео, и я предложу тебе варианты форматов для скачивания.")

@dp.message_handler(lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
async def get_formats(message: Message):
    url = message.text.strip()
    
    # Получение форматов видео с помощью yt-dlp
    ydl_opts = {'quiet': True, 'listformats': True}
    formats = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict['formats']
        
        # Разделяем форматы на доступные и недоступные по размеру
        available_formats = []
        unavailable_formats = []

        for fmt in formats:
            file_size = fmt['filesize'] or 0
            file_size_mb = file_size / (1024 * 1024)
            size_display = f"{file_size_mb:.2f} MB" if file_size > 0 else "N/A"
            format_line = f"{fmt['format_id']} - {fmt['ext']} - {fmt['format_note']} - {size_display}"
            
            # Проверка на размер файла
            if file_size > TELEGRAM_FILE_SIZE_LIMIT:
                unavailable_formats.append(format_line)  # Недоступные форматы
            else:
                available_formats.append(format_line)  # Доступные форматы

        # Формируем сообщение со списком доступных и недоступных форматов
        format_message = "Доступные для скачивания форматы:\n"
        format_message += "\n".join(available_formats) or "Нет доступных форматов для скачивания.\n"
        
        if unavailable_formats:
            format_message += "\n\nНедоступные форматы (размер > 50 MB):\n"
            format_message += "\n".join(unavailable_formats)
            format_message += "\n\n*Эти форматы временно недоступны из-за ограничения Telegram на 50 MB.*"

        await message.reply(format_message)

    except Exception as e:
        await message.reply(f"Ошибка при получении форматов: {str(e)}")

@dp.message_handler(lambda message: message.text.isdigit())
async def download_video(message: Message):
    format_id = message.text.strip()
    url = message.reply_to_message.text.strip()  # предполагаем, что ответ на сообщение с ссылкой
    file_name = f"{message.from_user.id}_{format_id}.mp4"  # Уникальное имя файла для пользователя и формата
    
    # Проверка размера выбранного формата перед загрузкой
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            selected_format = next((fmt for fmt in info_dict['formats'] if fmt['format_id'] == format_id), None)
            if not selected_format:
                await message.reply("Формат не найден.")
                return

            file_size = selected_format['filesize'] or 0
            if file_size > TELEGRAM_FILE_SIZE_LIMIT:
                await message.reply("Извините, этот формат превышает лимит 50 MB и временно недоступен.")
                return

        # Опции для yt-dlp и загрузка файла
        ydl_opts = {
            'format': format_id,
            'outtmpl': file_name,
            'progress_hooks': [lambda d: asyncio.create_task(send_progress(d, message))],
            'quiet': True
        }

        await message.reply("Начинаю скачивание...")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Отправка файла после загрузки
        with open(file_name, 'rb') as video:
            await bot.send_document(message.chat.id, video)
        await message.reply("Загрузка завершена!")

    except Exception as e:
        await message.reply(f"Ошибка при загрузке: {str(e)}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)  # Удаление файла после отправки

async def send_progress(d, message):
    if d['status'] == 'downloading':
        # Обновление прогресса каждые 10%
        progress = d['_percent_str']
        if int(float(progress.strip('%'))) % 10 == 0:
            await message.reply(f"Прогресс: {progress}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
