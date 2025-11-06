import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ML_SERVER_URL = os.getenv('ML_SERVER_URL')  # URL для ML-сервера

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения"""
    user = update.message.from_user
    text = update.message.text
    
    logger.info(f"Текст от {user.first_name}: {text}")
    
    # Для текста просто возвращаем эхо
    response_text = f"📝 Вы написали: {text}"
    await update.message.reply_text(response_text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовые сообщения"""
    await process_media_message(update, "voice")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает аудио файлы"""
    await process_media_message(update, "audio")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает видео сообщения"""
    await process_media_message(update, "video")

async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает видео-заметки"""
    await process_media_message(update, "video_note")

async def process_media_message(update: Update, media_type: str):
    """Общая функция обработки медиа-сообщений"""
    user = update.message.from_user
    message = update.message
    
    # Проверяем, установлен ли ML_SERVER_URL
    if not ML_SERVER_URL:
        await message.reply_text("❌ ML-сервер не настроен. Сообщите администратору.")
        logger.error("ML_SERVER_URL не установлен!")
        return
    
    try:
        # Отправляем статус "печатает..."
        await update.message.chat.send_action(action="typing")
        
        # Получаем файл в зависимости от типа
        if media_type == "voice":
            file = await message.voice.get_file()
        elif media_type == "audio":
            file = await message.audio.get_file()
        elif media_type == "video":
            file = await message.video.get_file()
        elif media_type == "video_note":
            file = await message.video_note.get_file()
        else:
            await message.reply_text("❌ Неподдерживаемый тип медиа")
            return

        logger.info(f"Обработка {media_type} от {user.first_name}, file_id: {file.file_id}")
        
        # Скачиваем файл
        file_path = f"/tmp/{file.file_id}.ogg"
        await file.download_to_drive(file_path)
        
        # Отправляем на ML-сервер
        with open(file_path, 'rb') as f:
            files = {'file': (f'{file.file_id}.ogg', f, 'audio/ogg')}
            data = {'media_type': media_type}
            
            logger.info(f"Отправка запроса на ML-сервер: {ML_SERVER_URL}/process")
            
            response = requests.post(
                f"{ML_SERVER_URL}/process", 
                files=files, 
                data=data,
                timeout=300  # Таймаут 60 секунд
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('summary', 'Ответ от сервера без текста')
                await message.reply_text(response_text)
                logger.info(f"✅ Успешная обработка, ответ: {response_text[:100]}...")
            else:
                logger.error(f"Ошибка ML-сервера: {response.status_code} - {response.text}")
                await message.reply_text("❌ Ошибка при обработке аудио. Попробуйте позже.")
                
    except requests.exceptions.ConnectionError:
        logger.error("Не удалось подключиться к ML-серверу")
        await message.reply_text("🔌 ML-сервер недоступен. Проверьте подключение.")
    except requests.exceptions.Timeout:
        logger.error("Таймаут подключения к ML-серверу")
        await message.reply_text("⏰ Таймаут при обработке. Попробуйте позже.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка подключения к ML-серверу: {e}")
        await message.reply_text("🔌 Ошибка подключения к ML-серверу.")
    except Exception as e:
        logger.error(f"Общая ошибка: {e}", exc_info=True)
        await message.reply_text("❌ Произошла непредвиденная ошибка.")
    finally:
        # Удаляем временный файл
        try:
            if 'file_path' in locals():
                os.remove(file_path)
                logger.info("Временный файл удален")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ошибки"""
    logger.error(f"Ошибка при обработке сообщения: {context.error}", exc_info=True)

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return
    
    if not ML_SERVER_URL:
        logger.warning("ML_SERVER_URL не установлен! Бот будет работать без ML-функционала")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен и готов к работе!")
    if ML_SERVER_URL:
        logger.info(f"ML-сервер: {ML_SERVER_URL}")
    else:
        logger.info("ML-сервер: не настроен")
    
    application.run_polling()

if __name__ == '__main__':
    main()