import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Student, AuditLog, Setting, AttendanceSession, Subject
from ..schemas import UserCreateIn, StatusIn, SettingsIn
from ..security import require_roles, get_current_user, hash_password
from ..services import audit, notify, get_setting

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = Depends(require_roles("admin"))


def _out(u: User):
    return {"id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email, "role": u.role,
            "department": u.department, "status": u.status,
            "last_login": u.last_login.isoformat() if u.last_login else None}


@router.get("/users", dependencies=[admin_only])
def list_users(role: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if status:
        q = q.filter(User.status == status)
    return [_out(u) for u in q.order_by(User.role, User.username).all()]


@router.post("/users", status_code=201)
def create_user(data: UserCreateIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.role not in ("teacher", "admin"):
        raise HTTPException(400, "Role must be teacher or admin (students register themselves)")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(409, "Username already taken")
    u = User(username=data.username, password_hash=hash_password(data.password), full_name=data.full_name,
             email=data.email, department=data.department, role=data.role, status="active", must_change_password=True)
    db.add(u)
    db.flush()
    audit(db, admin, "user.create", "user", u.id, f"role={data.role}")
    db.commit()
    return _out(u)


@router.post("/users/{uid}/approve")
def approve(uid: int, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "User not found")
    u.status = "active"
    audit(db, admin, "user.approve", "user", uid)
    notify(db, uid, "Account approved", "You can now use Smart Attendance.", "approval")
    db.commit()
    return _out(u)


@router.post("/users/{uid}/status")
def set_status(uid: int, data: StatusIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.status not in ("active", "disabled"):
        raise HTTPException(400, "status must be active or disabled")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "User not found")
    if u.id == admin.id:
        raise HTTPException(400, "You cannot change your own status")
    u.status = data.status
    audit(db, admin, "user.status", "user", uid, data.status)
    db.commit()
    return _out(u)


@router.post("/users/{uid}/reset-password")
def reset_password(uid: int, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Used for 'forgot password': admin issues a one-time temporary password (shown once)."""
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "User not found")
    temp = secrets.token_urlsafe(7)
    u.password_hash = hash_password(temp)
    u.must_change_password = True
    u.failed_attempts, u.locked_until = 0, None
    audit(db, admin, "user.reset_password", "user", uid)
    db.commit()
    return {"temporary_password": temp}


@router.get("/audit", dependencies=[admin_only])
def audit_logs(action: Optional[str] = None, limit: int = 200, db: Session = Depends(get_db)):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action.like(f"{action}%"))
    return [{"id": a.id, "actor": a.actor_name, "action": a.action, "entity": a.entity, "entity_id": a.entity_id,
             "detail": a.detail, "at": a.created_at.isoformat(timespec="seconds")}
            for a in q.order_by(AuditLog.id.desc()).limit(min(limit, 500)).all()]


@router.get("/stats", dependencies=[admin_only])
def stats(db: Session = Depends(get_db)):
    c = lambda m, *f: db.query(func.count(m.id)).filter(*f).scalar() or 0
    return {"students": c(Student), "teachers": c(User, User.role == "teacher", User.status == "active"),
            "pending_users": c(User, User.status == "pending"), "subjects": c(Subject),
            "open_sessions": c(AttendanceSession, AttendanceSession.status == "open"),
            "finalized_sessions": c(AttendanceSession, AttendanceSession.status == "finalized"),
            "students_without_face": c(Student, Student.face_count == 0)}


# ---- settings (readable by any signed-in user; writable by admin) ----
@router.get("/settings")
def read_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"threshold": float(get_setting(db, "threshold")), "late_after_min": int(get_setting(db, "late_after_min"))}


@router.put("/settings")
def write_settings(data: SettingsIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    for k, v in (("threshold", data.threshold), ("late_after_min", data.late_after_min)):
        row = db.get(Setting, k)
        if row:
            row.value = str(v)
        else:
            db.add(Setting(key=k, value=str(v)))
    audit(db, admin, "settings.update", "settings", "", f"threshold={data.threshold} late_after={data.late_after_min}")
    db.commit()
    return {"threshold": data.threshold, "late_after_min": data.late_after_min}
