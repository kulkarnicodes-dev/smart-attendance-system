"""Shared business logic: audit, notifications, settings, rosters, permissions, statistics."""
import math
from collections import defaultdict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import (AuditLog, Notification, Setting, Student, Enrollment, TeacherAssignment,
                     AttendanceSession, AttendanceRecord, Subject, User)

ATTENDED = ("Present", "Late")
DEFAULT_SETTINGS = {"threshold": "75", "late_after_min": "10"}


# ---------- audit / notifications / settings ----------
def audit(db: Session, actor, action: str, entity: str = "", entity_id="", detail: str = ""):
    db.add(AuditLog(actor_id=getattr(actor, "id", None), actor_name=getattr(actor, "username", "system"),
                    action=action, entity=entity, entity_id=str(entity_id), detail=detail[:2000]))


def notify(db: Session, user_id, title: str, body: str = "", kind: str = "info"):
    if user_id:
        db.add(Notification(user_id=user_id, title=title[:120], body=body[:300], kind=kind))


def get_setting(db: Session, key: str) -> str:
    row = db.get(Setting, key)
    return row.value if row else DEFAULT_SETTINGS.get(key, "")


def threshold(db: Session) -> float:
    try:
        return float(get_setting(db, "threshold"))
    except ValueError:
        return 75.0


# ---------- roster & permissions ----------
def roster(db: Session, s: AttendanceSession):
    q = (db.query(Student).join(Enrollment, Enrollment.student_pk == Student.id)
         .filter(Enrollment.subject_id == s.subject_id))
    if s.division:
        q = q.filter(Student.division == s.division)
    return q.order_by(Student.roll_no).all()


def teacher_assigned(db: Session, user: User, subject_id: int, division: str = "") -> bool:
    if user.role == "admin":
        return True
    rows = db.query(TeacherAssignment).filter_by(teacher_id=user.id, subject_id=subject_id).all()
    return any(r.division == "" or r.division == division for r in rows)


def assigned_subject_ids(db: Session, user: User):
    if user.role == "admin":
        return None  # None = unrestricted
    return [r.subject_id for r in db.query(TeacherAssignment).filter_by(teacher_id=user.id).all()]


def can_manage_session(user: User, s: AttendanceSession) -> bool:
    return user.role == "admin" or s.teacher_id == user.id


def get_session_or_404(db: Session, sid: int) -> AttendanceSession:
    s = db.get(AttendanceSession, sid)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


def own_student(db: Session, user: User):
    return db.query(Student).filter(Student.user_id == user.id).first()


# ---------- statistics ----------
def needed_to_reach(attended: int, total: int, thr: float) -> int:
    """Consecutive lectures the student must attend to reach thr% (0 if already there)."""
    t = thr / 100
    if total == 0 or attended / total >= t or t >= 1:
        return 0
    return math.ceil((t * total - attended) / (1 - t))


def subject_stats(db: Session, student_pk: int):
    """Per-subject attendance for one student, using FINALIZED sessions only. Excused is excluded."""
    rows = (db.query(AttendanceRecord.status, AttendanceSession.subject_id)
            .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
            .filter(AttendanceRecord.student_pk == student_pk, AttendanceSession.status == "finalized").all())
    agg = defaultdict(lambda: {"attended": 0, "absent": 0, "excused": 0, "late": 0})
    for status, sub in rows:
        a = agg[sub]
        if status in ATTENDED:
            a["attended"] += 1
            if status == "Late":
                a["late"] += 1
        elif status == "Excused":
            a["excused"] += 1
        else:
            a["absent"] += 1
    thr = threshold(db)
    subs = {s.id: s for s in db.query(Subject).filter(Subject.id.in_(list(agg.keys()) or [0])).all()}
    out = []
    for sid, a in agg.items():
        total = a["attended"] + a["absent"]
        pct = round(a["attended"] * 100 / total, 1) if total else None
        out.append({"subject_id": sid, "subject": subs[sid].name, "code": subs[sid].code, **a, "total": total,
                    "percent": pct, "below": pct is not None and pct < thr,
                    "needed": needed_to_reach(a["attended"], total, thr)})
    out.sort(key=lambda x: x["subject"])
    return out


def overall(stats):
    att = sum(s["attended"] for s in stats)
    tot = sum(s["total"] for s in stats)
    return {"attended": att, "total": tot, "percent": round(att * 100 / tot, 1) if tot else None}
