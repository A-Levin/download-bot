import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
import yt_dlp
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in environment variables")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Настройки yt-dlp
ydl_opts = {
    'format': 'best',
    'progress_hooks': [],
}

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply(
        "Привет! Я бот для скачивания видео с YouTube.\n"
        "Просто отправь мне ссылку на видео, и я покажу доступные форматы для скачивания.\n"
        "⚠️ Ограничение: файлы до 50MB (ограничение Telegram)."
    )

@dp.message(lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
async def get_formats(message: Message):
    try:
        status_message = await message.reply("Получаю информацию о видео...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=False)
            
        available_formats = []
        unavailable_formats = []
        
        for f in info['formats']:
            if 'filesize' in f and f['filesize']:
                size_mb = f['filesize'] / (1024 * 1024)
                format_info = (
                    f"ID: {f['format_id']}\n"
                    f"Расширение: {f['ext']}\n"
                    f"Разрешение: {f.get('resolution', 'N/A')}\n"
                    f"Размер: {size_mb:.1f}MB"
                )
                
                if size_mb <= 50:
                    available_formats.append(format_info)
                else:
                    unavailable_formats.append(format_info)
        
        response = "🎥 Доступные форматы:\n\n"
        response += "\n\n".join(available_formats)
        
        if unavailable_formats:
            response += "\n\n❌ Недоступные форматы (>50MB):\n\n"
            response += "\n\n".join(unavailable_formats)
        
        await status_message.edit_text(response)
        
    except Exception as e:
        logger.error(f"Error processing YouTube link: {e}")
        await message.reply("Произошла ошибка при обработке ссылки. Попробуйте другое видео.")

@dp.message(lambda message: message.text and message.text.isdigit())
async def download_video(message: Message):
    try:
        format_id = message.text
        status_message = await message.reply("Начинаю загрузку...")
        
        async def progress_hook(d):
            if d['status'] == 'downloading':
                progress = float(d['downloaded_bytes']) / float(d['total_bytes']) * 100
                if progress % 10 < 1:  # Обновляем каждые 10%
                    await status_message.edit_text(f"Загрузка: {progress:.1f}%")
        
        ydl_opts['format'] = format_id
        ydl_opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)
        
        await bot.send_video(
            message.chat.id,
            video=open(filename, 'rb'),
            caption="Вот ваше видео!"
        )
        
        os.remove(filename)  # Удаляем файл после отправки
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await message.reply("Произошла ошибка при скачивании. Попробуйте другой формат.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
