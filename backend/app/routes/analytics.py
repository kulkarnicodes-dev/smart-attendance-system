import csv
import io
from collections import defaultdict
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (AttendanceRecord, AttendanceSession, Student, Subject, Enrollment, CorrectionRequest, User)
from ..security import get_current_user, require_roles
from ..services import (subject_stats, overall, threshold, needed_to_reach, own_student, assigned_subject_ids,
                        can_manage_session, get_session_or_404, ATTENDED, roster)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _student_access(user: User, db: Session, pk: int) -> Student:
    s = db.get(Student, pk)
    if not s:
        raise HTTPException(404, "Student not found")
    if user.role == "student" and s.user_id != user.id:   # never trust the ID in the URL
        raise HTTPException(403, "You can only view your own attendance")
    return s


@router.get("/me")
def my_summary(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    s = own_student(db, user)
    if not s:
        raise HTTPException(404, "No student profile linked to this account")
    return student_summary(s.id, user, db)


@router.get("/student/{pk}")
def student_summary(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    st = _student_access(user, db, pk)
    subs = subject_stats(db, pk)
    ov = overall(subs)
    thr = threshold(db)
    monthly = defaultdict(lambda: [0, 0])
    rows = (db.query(AttendanceRecord.status, AttendanceSession.date)
            .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
            .filter(AttendanceRecord.student_pk == pk, AttendanceSession.status == "finalized").all())
    for status, d in rows:
        if status == "Excused":
            continue
        m = monthly[d.strftime("%Y-%m")]
        m[1] += 1
        m[0] += status in ATTENDED
    return {"student": {"id": st.id, "name": st.name, "roll_no": st.roll_no, "division": st.division, "face_count": st.face_count},
            "threshold": thr, "overall": ov, "subjects": subs,
            "monthly": [{"month": k, "attended": v[0], "total": v[1], "percent": round(v[0] * 100 / v[1], 1)} for k, v in sorted(monthly.items())]}


@router.get("/student/{pk}/history")
def history(pk: int, subject_id: Optional[int] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _student_access(user, db, pk)
    q = (db.query(AttendanceRecord, AttendanceSession).join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
         .filter(AttendanceRecord.student_pk == pk, AttendanceSession.status == "finalized"))
    if subject_id:
        q = q.filter(AttendanceSession.subject_id == subject_id)
    pending = {c.session_id for c in db.query(CorrectionRequest).filter_by(student_pk=pk, status="pending").all()}
    out = []
    for r, s in q.order_by(AttendanceSession.date.desc(), AttendanceSession.start_time.desc()).limit(500).all():
        out.append({"session_id": s.id, "date": s.date.isoformat(), "start": s.start_time.strftime("%H:%M"),
                    "subject": s.subject.name, "status": r.status, "method": r.method, "note": r.note,
                    "correction_pending": s.id in pending})
    return out


@router.get("/overview", dependencies=[Depends(require_roles("admin", "teacher"))])
def overview(user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    thr = threshold(db)
    scope = assigned_subject_ids(db, user)
    q = (db.query(AttendanceRecord.student_pk, AttendanceRecord.status, AttendanceSession.subject_id, AttendanceSession.date)
         .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
         .filter(AttendanceSession.status == "finalized"))
    if scope is not None:
        q = q.filter(AttendanceSession.subject_id.in_(scope or [0]))
    cell = defaultdict(lambda: [0, 0])      # (student, subject) -> [attended, total]
    month = defaultdict(lambda: [0, 0])
    for pk, status, sub, d in q.all():
        if status == "Excused":
            continue
        c = cell[(pk, sub)]
        c[1] += 1
        c[0] += status in ATTENDED
        m = month[d.strftime("%Y-%m")]
        m[1] += 1
        m[0] += status in ATTENDED
    students = {s.id: s for s in db.query(Student).all()}
    subjects = {s.id: s for s in db.query(Subject).all()}
    below, per_sub, per_div = [], defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for (pk, sub), (att, tot) in cell.items():
        st = students.get(pk)
        if not st:
            continue
        per_sub[sub][0] += att; per_sub[sub][1] += tot
        per_div[st.division][0] += att; per_div[st.division][1] += tot
        pct = att * 100 / tot
        if pct < thr:
            below.append({"student_pk": pk, "name": st.name, "roll_no": st.roll_no, "division": st.division,
                          "subject": subjects[sub].name, "percent": round(pct, 1), "attended": att, "total": tot,
                          "needed": needed_to_reach(att, tot, thr)})
    below.sort(key=lambda x: x["percent"])
    pct = lambda v: round(v[0] * 100 / v[1], 1) if v[1] else 0
    return {"threshold": thr, "below": below,
            "by_subject": [{"subject": subjects[k].name, "code": subjects[k].code, "percent": pct(v)} for k, v in per_sub.items()],
            "by_division": [{"division": k or "-", "percent": pct(v)} for k, v in sorted(per_div.items())],
            "monthly": [{"month": k, "percent": pct(v)} for k, v in sorted(month.items())]}


@router.get("/subject/{sub_id}", dependencies=[Depends(require_roles("admin", "teacher"))])
def subject_summary(sub_id: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    scope = assigned_subject_ids(db, user)
    if scope is not None and sub_id not in scope:
        raise HTTPException(403, "You are not assigned to this subject")
    thr = threshold(db)
    out = []
    for st in db.query(Student).join(Enrollment, Enrollment.student_pk == Student.id).filter(Enrollment.subject_id == sub_id).order_by(Student.roll_no):
        row = next((x for x in subject_stats(db, st.id) if x["subject_id"] == sub_id), None)
        out.append({"student_pk": st.id, "roll_no": st.roll_no, "name": st.name, "division": st.division,
                    "attended": row["attended"] if row else 0, "total": row["total"] if row else 0,
                    "percent": row["percent"] if row else None, "below": bool(row and row["below"])})
    return {"threshold": thr, "students": out}


# ---------------- CSV exports ----------------
def _csv(name, rows):
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={name}"})


@router.get("/export/session/{sid}")
def export_session(sid: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    s = get_session_or_404(db, sid)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    recs = {r.student_pk: r for r in db.query(AttendanceRecord).filter_by(session_id=sid).all()}
    rows = [["Roll No", "Name", "Division", "Status", "Time", "Method", "Confidence", "Note"]]
    for st in roster(db, s):
        r = recs.get(st.id)
        rows.append([st.roll_no, st.name, st.division, r.status if r else "Not marked", r.time if r and r.time else "",
                     r.method if r else "", round(r.confidence or 0, 3) if r else "", r.note if r else ""])
    return _csv(f"session_{s.subject.code}_{s.date}.csv", rows)


@router.get("/export/subject/{sub_id}")
def export_subject(sub_id: int, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    scope = assigned_subject_ids(db, user)
    if scope is not None and sub_id not in scope:
        raise HTTPException(403, "You are not assigned to this subject")
    sub = db.get(Subject, sub_id)
    if not sub:
        raise HTTPException(404, "Subject not found")
    sessions = (db.query(AttendanceSession).filter_by(subject_id=sub_id, status="finalized")
                .order_by(AttendanceSession.date, AttendanceSession.start_time).all())
    recs = defaultdict(dict)
    for r in db.query(AttendanceRecord).filter(AttendanceRecord.session_id.in_([s.id for s in sessions] or [0])).all():
        recs[r.student_pk][r.session_id] = r.status
    rows = [["Roll No", "Name", "Division"] + [f"{s.date} {s.start_time:%H:%M}" for s in sessions] + ["Attended", "Total", "Percent"]]
    for st in db.query(Student).join(Enrollment, Enrollment.student_pk == Student.id).filter(Enrollment.subject_id == sub_id).order_by(Student.roll_no):
        marks = [recs[st.id].get(s.id, "-") for s in sessions]
        att = sum(m in ATTENDED for m in marks)
        tot = sum(m in ("Present", "Late", "Absent") for m in marks)
        rows.append([st.roll_no, st.name, st.division] + [m[:1] if m != "-" else "-" for m in marks] + [att, tot, f"{att * 100 / tot:.1f}%" if tot else "-"])
    return _csv(f"subject_{sub.code}.csv", rows)


@router.get("/export/student/{pk}")
def export_student(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    st = _student_access(user, db, pk)
    rows = [["Date", "Time", "Subject", "Status", "Method", "Note"]]
    for h in history(pk, None, user, db):
        rows.append([h["date"], h["start"], h["subject"], h["status"], h["method"], h["note"]])
    return _csv(f"attendance_{st.roll_no}.csv", rows)
