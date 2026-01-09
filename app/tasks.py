from app.celery_app import celery_app
from faster_whisper import WhisperModel

print("Loading Faster-Whisper model in Celery worker (base, int8)...")
model = WhisperModel("base", device="cpu", compute_type="int8")


@celery_app.task(bind=True)
def transcribe_audio(self, file_path: str):
    segments, info = model.transcribe(file_path, beam_size=5)
    text = " ".join([seg.text for seg in segments]).strip()
    language = info.get("language", "unknown") if isinstance(info, dict) else "unknown"
    return {
        "text": text,
        "language": language
    }
