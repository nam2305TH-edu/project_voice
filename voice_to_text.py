#  uvicorn app.streaming_server:app --reload --host 0.0.0.0 --port 8001 
from gtts import gTTS
from pathlib import Path


text = "what your name"

tts = gTTS(text=text, lang='en')
output_file = Path("test_en30s.mp3")
tts.save(output_file)

print(f"Đã tạo file audio: {output_file}")
