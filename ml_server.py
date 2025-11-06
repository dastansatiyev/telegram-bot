import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import whisper
from transformers import pipeline
import tempfile
import torch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audio Processing API")

# Разрешаем CORS для всех источников (для тестирования)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные для моделей
model_whisper = None
model_summarizer = None

def load_models():
    """Загрузка моделей при старте сервера"""
    global model_whisper, model_summarizer
    
    logger.info("🔄 Загрузка моделей...")
    
    try:
        # Загружаем Whisper модель (используем base для баланса скорость/качество)
        logger.info("Загрузка Whisper model...")
        model_whisper = whisper.load_model("base")
        
        # Загружаем модель для суммаризации (русский язык)
        logger.info("Загрузка модели для суммаризации...")
        model_summarizer = pipeline(
            "summarization", 
            model="IlyaGusev/rut5_base_sum_gazeta",
            tokenizer="IlyaGusev/rut5_base_sum_gazeta"
        )
        
        logger.info("✅ Модели успешно загружены!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки моделей: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Загрузка моделей при старте сервера"""
    load_models()

@app.get("/")
async def root():
    """Проверка работы сервера"""
    return {"status": "OK", "message": "Audio Processing API работает"}

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера и моделей"""
    models_loaded = model_whisper is not None and model_summarizer is not None
    return {
        "status": "healthy" if models_loaded else "unhealthy",
        "models_loaded": models_loaded,
        "whisper_loaded": model_whisper is not None,
        "summarizer_loaded": model_summarizer is not None
    }

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    media_type: str = Form(...)
):
    """
    Обрабатывает аудио/видео файл: транскрибирует и создает краткое содержание
    """
    if not model_whisper or not model_summarizer:
        raise HTTPException(status_code=503, detail="Модели не загружены")
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        logger.info(f"🔊 Начата обработка {media_type} файла")
        
        # 1. Транскрибация с помощью Whisper
        logger.info("Транскрибация аудио...")
        result = model_whisper.transcribe(temp_path, fp16=torch.cuda.is_available())
        transcribed_text = result["text"].strip()
        
        logger.info(f"Транскрибированный текст: {transcribed_text}")
        
        if not transcribed_text:
            return {
                "summary": "❌ Не удалось распознать речь в сообщении",
                "transcribed_text": ""
            }

        # 2. Суммаризация текста
        logger.info("Создание краткого содержания...")
        
        # Если текст короткий, просто возвращаем его
        if len(transcribed_text.split()) < 20:
            summary_text = transcribed_text
        else:
            # Суммаризируем только если текст достаточно длинный
            summary_result = model_summarizer(
                transcribed_text, 
                max_length=150, 
                min_length=30, 
                do_sample=False
            )
            summary_text = summary_result[0]['summary_text']

        logger.info("✅ Обработка завершена успешно")
        
        return {
            "summary": f"**Транскрипция:** {transcribed_text}\n\n**Краткое содержание:** {summary_text}",
            "transcribed_text": transcribed_text,
            "summary_short": summary_text
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)