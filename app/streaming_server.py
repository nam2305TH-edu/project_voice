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
CHUNK_DURATION = 0.5
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

@app.websocket("/stt")
async def websocket_stt(ws: WebSocket):
    await ws.accept()
    audio_buffer = []

    try:
        while True:
            data = await ws.receive_bytes()
            chunk = np.frombuffer(data, dtype=np.float32)
            audio_buffer.append(chunk)
            total_samples = sum(len(c) for c in audio_buffer)

            if len(audio_buffer) > 0:  # gửi liên tục từng chunk
                audio_array = np.concatenate(audio_buffer)
                loop = asyncio.get_running_loop()
                segments, _ = await loop.run_in_executor(
                    None,
                    lambda: model.transcribe(audio_array, beam_size=5)
                )
                text = " ".join([seg.text for seg in segments])
                await ws.send_text(json.dumps({"text": text}))
                audio_buffer = []  # reset buffer

    except WebSocketDisconnect:
        print("Client disconnected")
        if audio_buffer:
            audio_array = np.concatenate(audio_buffer)
            loop = asyncio.get_running_loop()
            segments, _ = await loop.run_in_executor(
                None,
                lambda: model.transcribe(audio_array, beam_size=5)
            )
            text = " ".join([seg.text for seg in segments])
            print("Final transcription:", text)
