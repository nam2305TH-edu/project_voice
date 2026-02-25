# Tme AI Agent - Voice Engine

Hệ thống AI Agent hỗ trợ giọng nói với khả năng Speech-to-Text (STT) realtime, tìm kiếm thông tin và trả lời câu hỏi thông minh.

## 📋 Tính năng chính

- **Speech-to-Text Realtime**: Chuyển đổi giọng nói thành văn bản theo thời gian thực qua WebSocket
- **AI Brain**: Xử lý câu hỏi và trả lời thông minh sử dụng LLM (Llama 3.1 via Groq)
- **Tìm kiếm Web**: Tích hợp Tavily API để tìm kiếm thông tin realtime
- **Vector Database**: Lưu trữ và truy vấn ngữ cảnh với ChromaDB
- **Horizontal Scaling**: Hỗ trợ scale workers với Kafka message queue
- **Notification**: Thông báo qua Telegram bot
- **Monitoring**: Giám sát hệ thống với Prometheus

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI, Uvicorn |
| STT Engine | Faster-Whisper |
| LLM | Llama 3.1 (via Groq API) |
| Search | Tavily API |
| Vector DB | ChromaDB |
| Message Queue | Apache Kafka |
| Task Queue | Celery + Redis |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| Monitoring | Prometheus |
| Orchestration | Apache Airflow |
| Container | Docker, Docker Compose |

## 📁 Cấu trúc Project

```
Project_voice/
├── API/
│   ├── Search_OpenAI/          # Module Brain & Search
│   │   ├── brain.py            # Core AI Brain logic
│   │   ├── search.py           # Search manager
│   │   ├── database.py         # Database operations
│   │   ├── news_service.py     # News scraping service
│   │   └── telegram_service.py # Telegram notifications
│   └── voice/                  # Module Voice Processing
│       ├── main.py             # FastAPI app entry
│       ├── model_loader.py     # Whisper model loader
│       ├── audio_utils.py      # Audio processing utilities
│       ├── tasks.py            # Celery tasks
│       └── routes/             # API routes
│           ├── stt.py          # Speech-to-Text endpoints
│           ├── search.py       # Search endpoints
│           └── metrics.py      # Prometheus metrics
├── dags/                       # Airflow DAGs
├── data/                       # Data storage (ChromaDB, SQLite)
├── deploy/                     # Deployment configs
├── font_end/                   # Frontend (HTML/JS)
├── temp_audio/                 # Temporary audio files
├── config.py                   # Configuration
├── kafka_worker.py             # Kafka consumer worker
├── kafka_monitor.py            # Kafka monitoring
├── scheduler.py                # Task scheduler
├── docker-compose.yaml         # Docker orchestration
└── requirements.txt            # Python dependencies
```

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.10+
- Docker & Docker Compose
- Redis (cho Celery)
- Kafka (cho message queue)

### 1. Clone và cài đặt dependencies

```bash
git clone <repository-url>
cd Project_voice
pip install -r requirements.txt
```

### 2. Cấu hình environment variables

Tạo file `.env`:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Celery (Optional)
USE_CELERY=false

# Data Management
MAX_DATA_SIZE_MB=1024
CLEANUP_DAYS=30
```

### 3. Chạy với Docker Compose (Recommended)

```bash
docker-compose up -d
```

Services sẽ chạy trên:
- **STT API**: http://localhost:8000
- **ChromaDB**: http://localhost:8001
- **Kafka**: localhost:9092
- **Prometheus**: http://localhost:9090

### 4. Chạy local (Development)

```bash
# Chạy API server
uvicorn API.voice.main:app --host 0.0.0.0 --port 8000 --reload

# Chạy Kafka worker (trong terminal khác)
python kafka_worker.py
```

## 📡 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/v1/stt` | Upload audio file for transcription |
| POST | `/v1/search` | Search query |
| GET | `/v1/metrics` | Prometheus metrics |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/v1/stt` | Realtime speech-to-text streaming |

### Ví dụ sử dụng WebSocket STT

```javascript
const ws = new WebSocket('ws://localhost:8000/v1/stt');

// Gửi audio chunks
ws.send(audioChunk); // Int16 PCM, 16kHz

// Nhận transcription
ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    console.log(result.text);
};
```

## ⚙️ Configuration

Các tham số trong `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `_SAMPLE_` | 16000 | Sample rate (Hz) |
| `_MIN_` | 0.3 | Minimum audio length (s) |
| `_MAX_` | 1.5 | Maximum audio chunk (s) |
| `_SILENCE_THRESHOLD_` | 0.002 | Silence detection threshold |
| `_SILENCE_DURATION_` | 0.4 | Silence duration to split (s) |

## 🔧 Scaling

### Horizontal Scaling với Kafka Workers

```bash
# Scale brain workers
docker-compose up -d --scale brain-worker=5
```

### Celery Workers (Alternative)

```bash
celery -A API.voice.celery_app worker --loglevel=info --concurrency=4
```

## 📊 Monitoring

### Prometheus Metrics

Access metrics tại: http://localhost:9090

Metrics bao gồm:
- Request latency
- Transcription time
- Error rates
- Worker status

### Kafka Monitoring

```bash
python kafka_monitor.py
```

## 🧪 Testing

### Stress Test với Locust

```bash
locust -f locustfile.py --host=http://localhost:8000
```

### Evaluation Pipeline

```bash
python evaluation_pipeline.py
python analyze_evaluation.py
```

## 📦 Deployment

### Production Deployment

```bash
cd deploy
chmod +x deploy.sh
./deploy.sh
```

Hoặc sử dụng production compose:

```bash
docker-compose -f deploy/docker-compose.prod.yml up -d
```

## 🔄 Scheduled Tasks

### Airflow DAGs

- `tme_morning_refresh.py`: Cập nhật tin tức buổi sáng

### Manual News Refresh

```bash
python run_news_refresh.py
```

## 📝 License

MIT License

## 👥 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
