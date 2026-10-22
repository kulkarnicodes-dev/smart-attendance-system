from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (AttendanceSession, AttendanceRecord, Subject, User, TimetableEntry)
from ..schemas import SessionIn, MarkIn, FinalizeIn
from ..security import require_roles
from ..services import (audit, notify, roster, teacher_assigned, can_manage_session, get_session_or_404,
                        get_setting, subject_stats, threshold, assigned_subject_ids)

router = APIRouter(prefix="/api/sessions", tags=["sessions"], dependencies=[Depends(require_roles("admin", "teacher"))])
STATUSES = ("Present", "Absent", "Late", "Excused")


def _counts(db, sid):
    rows = db.query(AttendanceRecord.status, func.count(AttendanceRecord.id)).filter_by(session_id=sid).group_by(AttendanceRecord.status).all()
    return {k: v for k, v in rows}


def _out(s: AttendanceSession, c=None, roster_n=None):
    return {"id": s.id, "subject_id": s.subject_id, "subject": s.subject.name, "code": s.subject.code,
            "teacher_id": s.teacher_id, "teacher": s.teacher.full_name or s.teacher.username,
            "division": s.division, "date": s.date.isoformat(), "start": s.start_time.strftime("%H:%M"),
            "duration_min": s.duration_min, "topic": s.topic, "status": s.status, "late_after_min": s.late_after_min,
            "counts": c or {}, "roster": roster_n}


def _create(db, user, subject_id, division, d, start, duration, topic, teacher_id=None, timetable_id=None):
    sub = db.get(Subject, subject_id)
    if not sub:
        raise HTTPException(400, "Subject not found")
    tid = teacher_id if (user.role == "admin" and teacher_id) else user.id
    t = db.get(User, tid)
    if user.role == "teacher" and not teacher_assigned(db, user, subject_id, division):
        raise HTTPException(403, "You are not assigned to this subject/division")
    if user.role == "admin" and (not t or t.role not in ("teacher", "admin")):
        raise HTTPException(400, "Teacher required")
    if db.query(AttendanceSession).filter_by(subject_id=subject_id, division=division, date=d, start_time=start).first():
        raise HTTPException(409, "A session for this subject, division, date and time already exists")
    s = AttendanceSession(subject_id=subject_id, teacher_id=tid, division=division, date=d, start_time=start,
                          duration_min=duration, topic=topic, status="open", timetable_id=timetable_id,
                          late_after_min=int(get_setting(db, "late_after_min") or 10))
    db.add(s)
    db.flush()
    audit(db, user, "session.create", "session", s.id, f"{sub.code} {d} {start:%H:%M} div={division or 'all'}")
    db.commit()
    db.refresh(s)
    return s


@router.post("", status_code=201)
def create_session(d: SessionIn, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    try:
        start = datetime.strptime(d.start_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(400, "Time must be HH:MM")
    s = _create(db, user, d.subject_id, d.division, d.date, start, d.duration_min, d.topic, d.teacher_id)
    return _out(s, roster_n=len(roster(db, s)))


@router.post("/from-timetable/{eid}", status_code=201)
def from_timetable(eid: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    e = db.get(TimetableEntry, eid)
    if not e:
        raise HTTPException(404, "Timetable entry not found")
    if user.role == "teacher" and e.teacher_id != user.id:
        raise HTTPException(403, "This lecture belongs to another teacher")
    existing = db.query(AttendanceSession).filter_by(subject_id=e.subject_id, division=e.division,
                                                     date=date.today(), start_time=e.start_time).first()
    s = existing or _create(db, user, e.subject_id, e.division, date.today(), e.start_time, e.duration_min, "",
                            e.teacher_id, e.id)
    return _out(s, roster_n=len(roster(db, s)))


@router.get("")
def list_sessions(status: Optional[str] = None, subject_id: Optional[int] = None, on_date: Optional[date] = None,
                  user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    q = db.query(AttendanceSession)
    if user.role == "teacher":
        q = q.filter(AttendanceSession.teacher_id == user.id)
    if status:
        q = q.filter(AttendanceSession.status == status)
    if subject_id:
        q = q.filter(AttendanceSession.subject_id == subject_id)
    if on_date:
        q = q.filter(AttendanceSession.date == on_date)
    rows = q.order_by(AttendanceSession.date.desc(), AttendanceSession.start_time.desc()).limit(200).all()
    return [_out(s, _counts(db, s.id), len(roster(db, s))) for s in rows]


def _detail(db, s):
    recs = {r.student_pk: r for r in db.query(AttendanceRecord).filter_by(session_id=s.id).all()}
    students = roster(db, s)
    items = []
    for st in students:
        r = recs.get(st.id)
        items.append({"student_pk": st.id, "roll_no": st.roll_no, "name": st.name, "division": st.division,
                      "face_count": st.face_count,
                      "status": r.status if r else None, "method": r.method if r else None,
                      "time": r.time.strftime("%H:%M:%S") if r and r.time else None,
                      "confidence": round(r.confidence or 0, 3) if r else None, "note": r.note if r else ""})
    c = _counts(db, s.id)
    return {**_out(s, c, len(students)), "students": items, "unmarked": sum(1 for i in items if i["status"] is None)}


@router.get("/{sid}")
def session_detail(sid: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    s = get_session_or_404(db, sid)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    return _detail(db, s)


@router.post("/{sid}/mark")
def manual_mark(sid: int, d: MarkIn, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    s = get_session_or_404(db, sid)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    if d.status not in STATUSES:
        raise HTTPException(400, f"status must be one of {', '.join(STATUSES)}")
    if d.student_pk not in {st.id for st in roster(db, s)}:
        raise HTTPException(400, "Student is not on this session's roster")
    reason = d.reason.strip()
    rec = db.query(AttendanceRecord).filter_by(session_id=sid, student_pk=d.student_pk).first()
    if (s.status == "finalized" or (rec and rec.status != d.status and rec.method == "face")) and len(reason) < 5:
        raise HTTPException(400, "A reason (min 5 characters) is required to change a recorded attendance")
    old = rec.status if rec else None
    if rec:
        rec.status, rec.method, rec.note, rec.time = d.status, "manual", reason[:255], datetime.now().time().replace(microsecond=0)
    else:
        rec = AttendanceRecord(session_id=sid, student_pk=d.student_pk, status=d.status, method="manual",
                               note=reason[:255], time=datetime.now().time().replace(microsecond=0))
        db.add(rec)
    if s.status == "finalized" or old is not None:
        audit(db, user, "attendance.change", "session", sid, f"student={d.student_pk} {old}->{d.status} reason={reason}")
    db.commit()
    return {"ok": True, "status": d.status}


@router.post("/{sid}/finalize")
def finalize(sid: int, d: FinalizeIn, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    """Locks the session. Students without a record become Absent ONLY if the teacher confirms."""
    s = get_session_or_404(db, sid)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    if s.status == "finalized":
        raise HTTPException(409, "Session already finalized")
    students = roster(db, s)
    have = {r.student_pk for r in db.query(AttendanceRecord).filter_by(session_id=sid).all()}
    missing = [st for st in students if st.id not in have]
    if missing and not d.confirm_absent:
        raise HTTPException(409, f"{len(missing)} student(s) have no attendance yet. Confirm to mark them Absent.")
    try:
        for st in missing:
            db.add(AttendanceRecord(session_id=sid, student_pk=st.id, status="Absent", method="finalize"))
        s.status, s.finalized_at = "finalized", datetime.utcnow()
        audit(db, user, "session.finalize", "session", sid, f"auto_absent={len(missing)}")
        db.flush()
        thr = threshold(db)
        recs = {r.student_pk: r.status for r in db.query(AttendanceRecord).filter_by(session_id=sid).all()}
        for st in students:
            if st.user_id and recs.get(st.id) == "Absent":
                notify(db, st.user_id, f"Absent: {s.subject.name}", f"You were marked absent on {s.date} {s.start_time:%H:%M}. "
                       "You can request a correction from the Corrections page.", "absence")
            if st.user_id and recs.get(st.id) in ("Absent",):
                for sub in subject_stats(db, st.id):
                    if sub["subject_id"] == s.subject_id and sub["below"]:
                        notify(db, st.user_id, f"Low attendance: {sub['subject']}",
                               f"Your attendance is {sub['percent']}% (minimum {thr:g}%). Attend {sub['needed']} more lectures in a row to recover.",
                               "low_attendance")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return _detail(db, s)


@router.delete("/{sid}")
def delete_session(sid: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    s = get_session_or_404(db, sid)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    if s.status == "finalized" and user.role != "admin":
        raise HTTPException(403, "Only an admin can delete a finalized session")
    audit(db, user, "session.delete", "session", sid, f"{s.subject.code} {s.date}")
    db.delete(s)
    db.commit()
    return {"ok": True}
