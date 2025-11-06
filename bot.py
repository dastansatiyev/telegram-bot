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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все входящие сообщения и возвращает их обратно"""
    user = update.message.from_user
    chat_id = update.message.chat_id
    message_type = update.message.content_type
    
    logger.info(f"Получено сообщение от {user.first_name} (ID: {user.id}) в чате {chat_id}, тип: {message_type}")
    
    # В зависимости от типа контента, обрабатываем по-разному
    if message_type == 'text':
        response_text = f"📝 Вы написали: {update.message.text}"
        await update.message.reply_text(response_text)
    
    elif message_type == 'voice':
        await update.message.reply_text("🎤 Вы отправили голосовое сообщение")
        # Можно получить файл голосового сообщения
        voice_file = await update.message.voice.get_file()
        logger.info(f"Голосовое сообщение: {voice_file.file_path}")
    
    elif message_type == 'audio':
        await update.message.reply_text("🎵 Вы отправили аудио файл")
    
    elif message_type == 'video':
        await update.message.reply_text("🎥 Вы отправили видео сообщение")
    
    elif message_type == 'video_note':
        await update.message.reply_text("📹 Вы отправили видео-заметку (круглое видео)")
    
    else:
        await update.message.reply_text(f"🤖 Я получил ваше сообщение типа: {message_type}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ошибки"""
    logger.error(f"Ошибка при обработке сообщения: {context.error}")

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен! Убедитесь, что переменная окружения BOT_TOKEN задана.")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик для всех типов сообщений
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()