import shutil
import os
import asyncio
import whisper

from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.middleware import TimingMiddleware
from app.config import USE_CELERY
from app.tasks import transcribe_audio
from pydub import AudioSegment   # <<< QUAN TRỌNG (ffmpeg)

app = FastAPI(title="Tme AI Agent - Voice Engine")

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

if not USE_CELERY:
    print("Loading Whisper Model...")
    model = whisper.load_model("base")

app.add_middleware(TimingMiddleware)

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Nhận file âm thanh, trả về:
    - text
    - duration (giây)
    - filename
    - file size
    """

    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a")):
        raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ")

    file_path = TEMP_DIR / file.filename
    wav_path = file_path.with_suffix(".wav")

    try:

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size


        audio = AudioSegment.from_file(file_path)
        duration = len(audio) / 1000.0  

        if duration > 30:
            raise HTTPException(
                status_code=400,
                detail=f"File quá dài ({duration:.1f}s). Tối đa 30 giây."
            )


        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")

        if USE_CELERY:
            task = transcribe_audio.delay(str(wav_path))
            return {
                "status": "queued",
                "task_id": task.id,
                "filename": file.filename,
                "duration": duration,
                "size_bytes": file_size, 
                
            }
            timeout = 10

        # -------------------------
        # 5. Whisper Transcribe
        # -------------------------
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(str(wav_path))
        )

        return {
            "status": "success",
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "filename": file.filename,
            "duration": duration,
            "size_bytes": file_size
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if file_path.exists():
            os.remove(file_path)
        if wav_path.exists():
            os.remove(wav_path)


@app.get("/v1/stt/result/{task_id}")
def get_task_result(task_id: str):
    task = transcribe_audio.AsyncResult(task_id)

    if task.state == "SUCCESS":
        return {
            "status": "success",
            "result": task.result
        }
    return {
        "status": task.state
    }
