from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Notification, User
from ..security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def mine(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Notification).filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(60).all()
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"unread": unread, "items": [{"id": n.id, "kind": n.kind, "title": n.title, "body": n.body, "read": n.is_read,
                                          "at": n.created_at.isoformat(timespec="minutes")} for n in rows]}


@router.post("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.commit()
    return {"ok": True}
