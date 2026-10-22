from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine as db_engine, SessionLocal
from .models import User, Setting
from .security import hash_password
from .migrate import read_and_drop_legacy, restore_legacy
from .services import DEFAULT_SETTINGS
from .routes import auth, admin, academics, timetable, students, sessions, recognition, corrections, analytics, notifications
from .face_service import DET_MODEL, REC_MODEL


@asynccontextmanager
async def lifespan(app: FastAPI):
    legacy = read_and_drop_legacy(db_engine)      # v1 -> v2 upgrade (no-op on fresh/new DBs)
    Base.metadata.create_all(bind=db_engine)
    db = SessionLocal()
    try:
        if legacy:
            restore_legacy(db, legacy)
        for k, v in DEFAULT_SETTINGS.items():
            if not db.get(Setting, k):
                db.add(Setting(key=k, value=v))
        if not db.query(User).filter(User.username == settings.ADMIN_USERNAME).first():
            db.add(User(username=settings.ADMIN_USERNAME, full_name="Administrator", role="admin", status="active",
                        password_hash=hash_password(settings.ADMIN_PASSWORD)))
            print(f"[setup] Created admin user '{settings.ADMIN_USERNAME}'")
        db.commit()
    finally:
        db.close()
    if not (DET_MODEL.exists() and REC_MODEL.exists()):
        print("[warning] Face models missing -> run: python scripts/download_models.py")
    yield


app = FastAPI(title="Smart Attendance System", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth, admin, academics, timetable, students, sessions, recognition, corrections, analytics, notifications):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "models_ready": DET_MODEL.exists() and REC_MODEL.exists(),
            "match_threshold": settings.MATCH_THRESHOLD}
