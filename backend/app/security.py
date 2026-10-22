from datetime import datetime, timedelta
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], hashed.encode())
    except ValueError:
        return False


def create_token(username: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": exp}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    if not cred:
        raise err
    try:
        payload = jwt.decode(cred.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise err
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or user.status != "active":
        raise err
    return user


# ---------- role guard + simple in-memory rate limit ----------
import time as _time
from collections import defaultdict as _dd
from fastapi import Request

_hits = _dd(list)


def require_roles(*roles):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action")
        return user
    return dep


def rate_limit(request: Request, bucket: str, max_calls: int, seconds: int):
    key = f"{bucket}:{request.client.host if request.client else 'x'}"
    now = _time.time()
    _hits[key] = [t for t in _hits[key] if now - t < seconds]
    if len(_hits[key]) >= max_calls:
        raise HTTPException(429, "Too many attempts. Please wait a few minutes and try again.")
    _hits[key].append(now)
