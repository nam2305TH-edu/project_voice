import sounddevice as sd
from scipy.io.wavfile import write
import requests
from pathlib import Path
import time
import asyncio
import websockets
import numpy as np

API_URL = "http://127.0.0.1:8000/v1/stt"
RESULT_URL = "http://127.0.0.1:8000/v1/stt/result"
WS_URL = "ws://127.0.0.1:8000/ws/stt"

TEMP_FILE = Path("recorded.wav")
DURATION = 3  
FS = 16000     
USE_STREAMING = True  

if USE_STREAMING:
    async def record_and_stream():
        async with websockets.connect(WS_URL) as ws:
            print("Bắt đầu ghi âm streaming... nhấn Ctrl+C để dừng")

            queue = asyncio.Queue()
            loop = asyncio.get_running_loop()


            def callback(indata, frames, time_info, status):
                audio_chunk = indata[:, 0].astype(np.float32).tobytes()
                asyncio.run_coroutine_threadsafe(queue.put(audio_chunk), loop)


            with sd.InputStream(channels=1, samplerate=FS, blocksize=1024, callback=callback):
                try:
                    while True:
                        chunk = await queue.get()
                        await ws.send(chunk)
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                            import json
                            data = json.loads(msg)
                            if data.get("text"):
                                print("Text streaming:", data["text"])
                        except asyncio.TimeoutError:
                            pass

                except KeyboardInterrupt:
                    print("Đã dừng ghi âm streaming.")

    asyncio.run(record_and_stream())

else:
    print(f"Ghi âm {DURATION} giây...")
    recording = sd.rec(int(DURATION*FS), samplerate=FS, channels=1)
    sd.wait()
    write(TEMP_FILE, FS, recording)
    print(f"Đã lưu file: {TEMP_FILE}")
    with open(TEMP_FILE, "rb") as f:
        response = requests.post(API_URL, files={"file": f})

    data = response.json()
    task_id = data.get("task_id")
    if not task_id:
        print("Lỗi API:", data)
        exit(1)

    print(f"Task đã được queue, task_id = {task_id}")

    while True:
        r = requests.get(f"{RESULT_URL}/{task_id}")
        res = r.json()

        if res["status"] == "success":
            print("Kết quả chuyển đổi:", res["result"]["text"])
            break
        elif res["status"] == "failure":
            print("Lỗi xử lý:", res.get("error"))
            break
        else:
            print("Đang xử lý...", res["status"])
            time.sleep(1)

    
    TEMP_FILE.unlink()
