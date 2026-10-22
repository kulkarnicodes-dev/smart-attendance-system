from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TimetableEntry, Subject, User, Enrollment, AttendanceSession
from ..schemas import TimetableIn
from ..security import require_roles, get_current_user
from ..services import audit, own_student

router = APIRouter(prefix="/api/timetable", tags=["timetable"])
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _parse(t: str):
    try:
        return datetime.strptime(t, "%H:%M").time()
    except ValueError:
        raise HTTPException(400, "Time must be HH:MM (24h)")


def _out(e: TimetableEntry):
    end = (datetime.combine(date.today(), e.start_time) + timedelta(minutes=e.duration_min)).time()
    return {"id": e.id, "subject_id": e.subject_id, "subject": e.subject.name, "code": e.subject.code,
            "teacher_id": e.teacher_id, "teacher": e.teacher.full_name or e.teacher.username,
            "division": e.division, "weekday": e.weekday, "day": DAYS[e.weekday],
            "start": e.start_time.strftime("%H:%M"), "end": end.strftime("%H:%M"),
            "duration_min": e.duration_min, "room": e.room}


def _overlap(a_start, a_dur, b_start, b_dur):
    d = date.today()
    a0 = datetime.combine(d, a_start); a1 = a0 + timedelta(minutes=a_dur)
    b0 = datetime.combine(d, b_start); b1 = b0 + timedelta(minutes=b_dur)
    return a0 < b1 and b0 < a1


@router.get("")
def list_timetable(division: Optional[str] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(TimetableEntry)
    if user.role == "student":
        st = own_student(db, user)
        if not st:
            return []
        subs = [e.subject_id for e in db.query(Enrollment).filter_by(student_pk=st.id).all()]
        q = q.filter(TimetableEntry.subject_id.in_(subs or [0]),
                     TimetableEntry.division.in_(["", st.division]))
    elif user.role == "teacher":
        q = q.filter(TimetableEntry.teacher_id == user.id)
    elif division:
        q = q.filter(TimetableEntry.division == division)
    return [_out(e) for e in sorted(q.all(), key=lambda e: (e.weekday, e.start_time))]


@router.get("/today")
def today_for_teacher(user: User = Depends(require_roles("teacher", "admin")), db: Session = Depends(get_db)):
    today = date.today()
    q = db.query(TimetableEntry).filter(TimetableEntry.weekday == today.weekday())
    if user.role == "teacher":
        q = q.filter(TimetableEntry.teacher_id == user.id)
    out = []
    for e in sorted(q.all(), key=lambda e: e.start_time):
        s = db.query(AttendanceSession).filter_by(subject_id=e.subject_id, division=e.division, date=today,
                                                  start_time=e.start_time).first()
        out.append({**_out(e), "session_id": s.id if s else None, "session_status": s.status if s else None})
    return out


@router.post("", status_code=201)
def create_entry(d: TimetableIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    start = _parse(d.start_time)
    if not db.get(Subject, d.subject_id):
        raise HTTPException(400, "Subject not found")
    t = db.get(User, d.teacher_id)
    if not t or t.role != "teacher":
        raise HTTPException(400, "Teacher not found")
    for e in db.query(TimetableEntry).filter_by(weekday=d.weekday).all():
        if not _overlap(start, d.duration_min, e.start_time, e.duration_min):
            continue
        if e.teacher_id == d.teacher_id:
            raise HTTPException(409, f"Conflict: this teacher already teaches {e.subject.code} at {e.start_time:%H:%M} that day")
        if d.room and e.room == d.room:
            raise HTTPException(409, f"Conflict: room {d.room} is used by {e.subject.code} at {e.start_time:%H:%M}")
        if e.division == d.division:
            raise HTTPException(409, f"Conflict: division {d.division or 'all'} already has {e.subject.code} at that time")
    row = TimetableEntry(subject_id=d.subject_id, teacher_id=d.teacher_id, division=d.division, weekday=d.weekday,
                         start_time=start, duration_min=d.duration_min, room=d.room)
    db.add(row)
    audit(db, a, "timetable.create", "subject", d.subject_id, f"{DAYS[d.weekday]} {d.start_time}")
    db.commit()
    db.refresh(row)
    return _out(row)


@router.delete("/{eid}")
def delete_entry(eid: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    e = db.get(TimetableEntry, eid)
    if not e:
        raise HTTPException(404, "Not found")
    db.delete(e)
    audit(db, a, "timetable.delete", "timetable", eid)
    db.commit()
    return {"ok": True}
