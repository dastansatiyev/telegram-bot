import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота будет браться из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения"""
    user = update.message.from_user
    text = update.message.text
    
    logger.info(f"Текст от {user.first_name}: {text}")
    response_text = f"📝 Вы написали: {text}"
    await update.message.reply_text(response_text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовые сообщения"""
    user = update.message.from_user
    voice = update.message.voice
    
    logger.info(f"Голосовое сообщение от {user.first_name}, duration: {voice.duration} сек")
    
    # Получаем информацию о файле
    voice_file = await voice.get_file()
    logger.info(f"Файл голосового сообщения: {voice_file.file_path}")
    
    await update.message.reply_text("🎤 Вы отправили голосовое сообщение")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает аудио файлы"""
    user = update.message.from_user
    audio = update.message.audio
    
    logger.info(f"Аудио файл от {user.first_name}, название: {audio.file_name}")
    await update.message.reply_text("🎵 Вы отправили аудио файл")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает видео сообщения"""
    user = update.message.from_user
    video = update.message.video
    
    logger.info(f"Видео от {user.first_name}, duration: {video.duration} сек")
    await update.message.reply_text("🎥 Вы отправили видео сообщение")

async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает видео-заметки (круглые видео)"""
    user = update.message.from_user
    video_note = update.message.video_note
    
    logger.info(f"Видео-заметка от {user.first_name}, duration: {video_note.duration} сек")
    await update.message.reply_text("📹 Вы отправили видео-заметку (круглое видео)")

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает неизвестные типы сообщений"""
    user = update.message.from_user
    logger.info(f"Неизвестный тип сообщения от {user.first_name}")
    await update.message.reply_text("🤖 Я получил ваше сообщение, но пока не знаю, как его обработать")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ошибки"""
    logger.error(f"Ошибка при обработке сообщения: {context.error}", exc_info=True)

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен! Убедитесь, что переменная окружения BOT_TOKEN задана.")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики для разных типов сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    application.add_handler(MessageHandler(filters.ALL, handle_unknown))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()