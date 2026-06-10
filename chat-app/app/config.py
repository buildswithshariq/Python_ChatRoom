import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR / 'chat.db'}"

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-abc123xyz")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "static"
