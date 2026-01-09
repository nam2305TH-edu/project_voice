import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.main import app as main_app       
from app.streaming_server import app as ws_app  
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Tme AI Agent - Unified Server")


app.mount("/static", StaticFiles(directory=str(BASE_DIR), html=True), name="static")

app.mount("/v1", main_app)      
app.mount("/ws", ws_app)         

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
