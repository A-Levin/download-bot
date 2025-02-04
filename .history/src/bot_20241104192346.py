import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
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

# Добавим словарь для хранения URL видео пользователей
user_video_urls = {}

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
        
        # Сохраняем URL для пользователя
        user_video_urls[message.from_user.id] = message.text
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=False)
            
        available_formats = []
        unavailable_formats = []
        
        for f in info['formats']:
            if 'filesize' in f and f['filesize']:
                size_mb = f['filesize'] / (1024 * 1024)
                format_info = (
                    f"📹 Формат #{f['format_id']}\n"
                    f"Расширение: {f['ext']}\n"
                    f"Разрешение: {f.get('resolution', 'N/A')}\n"
                    f"Размер: {size_mb:.1f}MB\n"
                    f"👉 /download_{f['format_id']}"
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

@dp.message(lambda message: message.text and message.text.startswith('/download_'))
async def download_video(message: Message):
    try:
        format_id = message.text.replace('/download_', '')
        logger.info(f"Download requested for format_id: {format_id}")
        
        if not message.from_user.id in user_video_urls:
            logger.warning(f"No video URL found for user {message.from_user.id}")
            await message.reply("Сначала отправьте ссылку на видео.")
            return
            
        video_url = user_video_urls[message.from_user.id]
        logger.info(f"Found video URL for user {message.from_user.id}: {video_url}")
        
        status_message = await message.reply("Начинаю загрузку...")
        logger.info("Status message sent")
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    progress = float(d['downloaded_bytes']) / float(d['total_bytes']) * 100
                    downloaded_mb = d['downloaded_bytes'] / (1024*1024)
                    total_mb = d['total_bytes'] / (1024*1024)
                    speed = d.get('speed', 0) / (1024*1024)  # Speed in MB/s
                    logger.info(f"Download progress: {progress:.1f}% ({downloaded_mb:.1f}MB/{total_mb:.1f}MB) Speed: {speed:.1f}MB/s")
                    if progress % 10 < 1:  # Обновляем каждые 10%
                        asyncio.create_task(status_message.edit_text(
                            f"Загрузка: {progress:.1f}%\n"
                            f"Скачано: {downloaded_mb:.1f}MB из {total_mb:.1f}MB\n"
                            f"Скорость: {speed:.1f}MB/s"
                        ))
                except Exception as e:
                    logger.error(f"Error in progress hook: {e}", exc_info=True)

        download_opts = {
            'format': format_id,
            'progress_hooks': [progress_hook],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,
        }
        
        logger.info(f"Starting download with options: {download_opts}")
        
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            logger.info("Extracting video info...")
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            logger.info(f"Download completed. Filename: {filename}")
            logger.debug(f"Video info: {info}")
        
        if not os.path.exists(filename):
            logger.error(f"File not found after download: {filename}")
            raise FileNotFoundError(f"Downloaded file not found: {filename}")
        
        file_size = os.path.getsize(filename)
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > 50 * 1024 * 1024:
            logger.warning(f"File too large ({file_size / (1024*1024):.2f} MB) for Telegram upload")
            await status_message.edit_text("Файл слишком большой для отправки через Telegram (>50MB). Попробуйте другой формат с меньшим качеством.")
            os.remove(filename)
            logger.info(f"Large file {filename} removed")
            return
            
        await status_message.edit_text("Загрузка завершена. Отправляю файл...")
        logger.info("Starting file upload to Telegram")
        
        try:
            logger.info("Preparing to send video")
            video = FSInputFile(filename)
            
            await bot.send_video(
                chat_id=message.chat.id,
                video=video,
                caption="Вот ваше видео!"
            )
            logger.info("Video successfully sent to Telegram")
            
            await status_message.edit_text("Видео успешно отправлено!")
            
        except Exception as e:
            logger.error(f"Error sending video: {str(e)}", exc_info=True)
            await message.reply(f"Ошибка при отправке видео: {str(e)}")
            raise
        finally:
            try:
                os.remove(filename)
                logger.info(f"File {filename} removed after processing")
            except Exception as e:
                logger.error(f"Error removing file {filename}: {str(e)}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Error in download_video: {str(e)}", exc_info=True)
        await message.reply(f"Произошла ошибка при скачивании. Попробуйте другой формат.\nОшибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
