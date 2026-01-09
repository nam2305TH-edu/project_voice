import os

USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"

REDIS_BROKER = "redis://localhost:6379/0"
REDIS_BACKEND = "redis://localhost:6379/1"
