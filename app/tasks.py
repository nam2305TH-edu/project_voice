import whisper
from app.celery_app import celery_app

print("Loading Whisper model in Celery worker...")
model = whisper.load_model("base")

@celery_app.task(bind=True)
def transcribe_audio(self, file_path: str):
    result = model.transcribe(file_path)
    return {
        "text": result["text"].strip(),
        "language": result.get("language", "unknown")
    }
