from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CorrectionRequest, AttendanceRecord, AttendanceSession, User
from ..schemas import CorrectionIn, DecisionIn
from ..security import get_current_user, require_roles
from ..services import audit, notify, own_student, roster, can_manage_session

router = APIRouter(prefix="/api/corrections", tags=["corrections"])


def _out(c: CorrectionRequest):
    s = c.session
    return {"id": c.id, "session_id": c.session_id, "subject": s.subject.name, "date": s.date.isoformat(),
            "start": s.start_time.strftime("%H:%M"), "student": c.student.name, "roll_no": c.student.roll_no,
            "requested_status": c.requested_status, "reason": c.reason, "status": c.status,
            "decision_note": c.decision_note, "created_at": c.created_at.isoformat(timespec="minutes")}


@router.post("", status_code=201)
def submit(d: CorrectionIn, user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    st = own_student(db, user)
    s = db.get(AttendanceSession, d.session_id)
    if not st or not s:
        raise HTTPException(404, "Session not found")
    if d.requested_status not in ("Present", "Late", "Excused"):
        raise HTTPException(400, "Requested status must be Present, Late or Excused")
    if s.status != "finalized" or st.id not in {x.id for x in roster(db, s)}:
        raise HTTPException(400, "You can only request corrections for finalized lectures you were enrolled in")
    rec = db.query(AttendanceRecord).filter_by(session_id=s.id, student_pk=st.id).first()
    if rec and rec.status == d.requested_status:
        raise HTTPException(400, "Your record already has that status")
    if db.query(CorrectionRequest).filter_by(session_id=s.id, student_pk=st.id, status="pending").first():
        raise HTTPException(409, "You already have a pending request for this lecture")
    c = CorrectionRequest(session_id=s.id, student_pk=st.id, requested_status=d.requested_status, reason=d.reason.strip())
    db.add(c)
    notify(db, s.teacher_id, "Correction request", f"{st.name} requested {d.requested_status} for {s.subject.name} ({s.date}).", "correction")
    audit(db, user, "correction.submit", "session", s.id, f"student={st.id} -> {d.requested_status}")
    db.commit()
    db.refresh(c)
    return _out(c)


@router.get("")
def list_requests(status: Optional[str] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(CorrectionRequest)
    if user.role == "student":
        st = own_student(db, user)
        q = q.filter(CorrectionRequest.student_pk == (st.id if st else 0))
    elif user.role == "teacher":
        q = q.join(AttendanceSession, AttendanceSession.id == CorrectionRequest.session_id).filter(AttendanceSession.teacher_id == user.id)
    if status:
        q = q.filter(CorrectionRequest.status == status)
    return [_out(c) for c in q.order_by(CorrectionRequest.id.desc()).limit(200).all()]


@router.post("/{cid}/decide")
def decide(cid: int, d: DecisionIn, user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    c = db.get(CorrectionRequest, cid)
    if not c:
        raise HTTPException(404, "Request not found")
    if not can_manage_session(user, c.session):
        raise HTTPException(403, "Only the session's teacher or an admin can decide this")
    if c.status != "pending":
        raise HTTPException(409, "Already decided")
    if not d.approve and len(d.note.strip()) < 3:
        raise HTTPException(400, "Please give a short reason when rejecting")
    c.status = "approved" if d.approve else "rejected"
    c.decided_by, c.decision_note, c.decided_at = user.id, d.note.strip()[:255], datetime.utcnow()
    if d.approve:
        rec = db.query(AttendanceRecord).filter_by(session_id=c.session_id, student_pk=c.student_pk).first()
        if rec:
            rec.status, rec.method, rec.note = c.requested_status, "correction", f"Approved request #{c.id}"
        else:
            db.add(AttendanceRecord(session_id=c.session_id, student_pk=c.student_pk, status=c.requested_status,
                                    method="correction", note=f"Approved request #{c.id}"))
    audit(db, user, f"correction.{c.status}", "correction", cid, f"student={c.student_pk} {c.requested_status} note={c.decision_note}")
    notify(db, c.student.user_id, f"Correction {c.status}", f"{c.session.subject.name} ({c.session.date}): {c.decision_note or c.status}", "correction")
    db.commit()
    return _out(c)
