import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import numpy as np
from faster_whisper import WhisperModel

app = FastAPI(title="project_voice")

model_size = "tiny"  
model = WhisperModel(model_size, device="cpu", compute_type="int8")
print(f"Model '{model_size}' loaded!")

SAMPLE_RATE = 16000

MIN_AUDIO_LENGTH = 0.15      
MAX_AUDIO_LENGTH = 1.5       
SILENCE_THRESHOLD = 0.008   
SILENCE_DURATION = 0.2       


def detect_voice_activity(audio: np.ndarray, threshold: float = SILENCE_THRESHOLD) -> bool:
    """Phát hiện có giọng nói hay không (VAD đơn giản)"""
    if len(audio) == 0:
        return False
    rms = np.sqrt(np.mean(audio ** 2))
    return rms > threshold

def find_silence_split(audio: np.ndarray, sample_rate: int, 
                       silence_duration: float = SILENCE_DURATION,
                       threshold: float = SILENCE_THRESHOLD) -> int:
    """Tìm vị trí im lặng để cắt audio (tránh cắt giữa từ)"""
    window_size = int(silence_duration * sample_rate)
    if len(audio) < window_size:
        return -1
    
    for i in range(len(audio) - window_size, max(0, len(audio) // 2), -int(sample_rate * 0.1)):
        window = audio[i:i + window_size]
        if not detect_voice_activity(window, threshold):
            return i + window_size // 2
    return -1


@app.websocket("/stt")
async def websocket_stt(ws: WebSocket):
    await ws.accept()
    print("Client connected for streaming STT")
    audio_buffer = np.array([], dtype=np.float32)
    
    full_text = ""
    silence_samples = 0
    
    loop = asyncio.get_running_loop()

    try:
        while True:
            data = await ws.receive_bytes()
            if len(data) % 2 == 0:
                chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            elif len(data) % 4 == 0:
                chunk = np.frombuffer(data, dtype=np.float32)
            else:
                continue
            
            audio_buffer = np.concatenate([audio_buffer, chunk])  
            has_voice = detect_voice_activity(chunk)
            
            if not has_voice:
                silence_samples += len(chunk)
            else:
                silence_samples = 0
            
            audio_duration = len(audio_buffer) / SAMPLE_RATE
            silence_duration_current = silence_samples / SAMPLE_RATE
            
            should_transcribe = (
                audio_duration >= MIN_AUDIO_LENGTH and 
                (silence_duration_current >= SILENCE_DURATION or audio_duration >= MAX_AUDIO_LENGTH)
            )
            
            if should_transcribe and len(audio_buffer) > 0:

                split_point = find_silence_split(audio_buffer, SAMPLE_RATE)
                
                if split_point > 0 and split_point < len(audio_buffer):
                    process_audio = audio_buffer[:split_point]
                    audio_buffer = audio_buffer[split_point:]
                else:
                    process_audio = audio_buffer
                    audio_buffer = np.array([], dtype=np.float32)
                
                silence_samples = 0
                
                try:
                    segments, _ = await loop.run_in_executor(
                        None,
                        lambda: model.transcribe(
                            process_audio, 
                            beam_size=1,           
                            vad_filter=False,      
                            without_timestamps=True 
                        )
                    )
                    
                    new_text = " ".join([seg.text for seg in segments]).strip()
                    
                    if new_text:
                        full_text = (full_text + " " + new_text).strip()
                    
                        await ws.send_text(json.dumps({
                            "partial": new_text,
                            "text": full_text,
                            "is_final": silence_duration_current >= SILENCE_DURATION
                        }))
                        
                except Exception as e:
                    print(f"Transcription error: {e}")
                    await ws.send_text(json.dumps({"error": str(e)}))
            
            elif audio_duration > 0.5 and audio_duration < MIN_AUDIO_LENGTH:
                await ws.send_text(json.dumps({
                    "status": "listening",
                    "buffer_duration": round(audio_duration, 2)
                }))

    except WebSocketDisconnect:
        print("Client disconnected")
        
        
        if len(audio_buffer) > SAMPLE_RATE * 0.2:  
            try:
                segments, _ = await loop.run_in_executor(
                    None,
                    lambda: model.transcribe(audio_buffer, beam_size=3, vad_filter=True)
                )
                final_text = " ".join([seg.text for seg in segments]).strip()
                if final_text:
                    full_text = (full_text + " " + final_text).strip()
                print(f"Final transcription: {full_text}")
            except Exception as e:
                print(f"Final transcription error: {e}")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
