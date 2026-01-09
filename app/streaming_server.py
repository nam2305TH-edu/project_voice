import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import numpy as np
from faster_whisper import WhisperModel

app = FastAPI(title="Tme AI Agent - Real-time STT")

print("Loading Faster-Whisper model...")
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5  # seconds per chunk for better accuracy
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

@app.websocket("/stt")
async def websocket_stt(ws: WebSocket):
    await ws.accept()
    audio_buffer = []

    try:
        while True:
            data = await ws.receive_bytes()
            # Interpret incoming buffer: prefer float32, fall back to int16
            if len(data) % 4 == 0:
                try:
                    chunk = np.frombuffer(data, dtype=np.float32)
                except Exception:
                    continue
            elif len(data) % 2 == 0:
                try:
                    tmp = np.frombuffer(data, dtype=np.int16)
                    chunk = tmp.astype(np.float32) / 32768.0
                except Exception:
                    continue
            else:
                # unknown payload length
                continue

            audio_buffer.append(chunk)
            total_samples = sum(len(c) for c in audio_buffer)

            # Only transcribe when we accumulated enough samples
            if total_samples >= CHUNK_SAMPLES:
                audio_array = np.concatenate(audio_buffer)
                audio_buffer = []

                loop = asyncio.get_running_loop()
                try:
                    segments, _ = await loop.run_in_executor(
                        None,
                        lambda: model.transcribe(audio_array, beam_size=5)
                    )
                    text = " ".join([seg.text for seg in segments])
                    await ws.send_text(json.dumps({"text": text}))
                except Exception as e:
                    await ws.send_text(json.dumps({"error": str(e)}))

    except WebSocketDisconnect:
        print("Client disconnected")
        if audio_buffer:
            audio_array = np.concatenate(audio_buffer)
            loop = asyncio.get_running_loop()
            try:
                segments, _ = await loop.run_in_executor(
                    None,
                    lambda: model.transcribe(audio_array, beam_size=5)
                )
                text = " ".join([seg.text for seg in segments])
                print("Final transcription:", text)
            except Exception as e:
                print("Final transcription error:", e)
