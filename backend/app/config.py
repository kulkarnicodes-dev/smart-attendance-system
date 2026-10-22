import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'attendance.db'}")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.45"))
    DETECT_THRESHOLD = float(os.getenv("DETECT_THRESHOLD", "0.85"))
    MAX_FACE_SAMPLES = int(os.getenv("MAX_FACE_SAMPLES", "25"))
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
    REVIEW_MARGIN = float(os.getenv("REVIEW_MARGIN", "0.07"))          # below threshold but within margin -> teacher review
    DUPLICATE_FACE_THRESHOLD = float(os.getenv("DUPLICATE_FACE_THRESHOLD", "0.65"))
    MIN_FACE_WIDTH_RATIO = float(os.getenv("MIN_FACE_WIDTH_RATIO", "0.10"))  # face must be >=10% of frame width
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "10"))
    MODEL_DIR = BASE_DIR / "models"


settings = Settings()
