from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..face_service import engine, ModelsMissing
from ..models import Student, AttendanceRecord
from ..schemas import IdentifyIn
from ..security import require_roles
from ..services import roster, can_manage_session, get_session_or_404

router = APIRouter(prefix="/api/recognition", tags=["recognition"])


@router.post("/identify")
def identify(data: IdentifyIn, user=Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    """One camera frame for an OPEN session. Only enrolled students on the roster are ever marked."""
    s = get_session_or_404(db, data.session_id)
    if not can_manage_session(user, s):
        raise HTTPException(403, "This session belongs to another teacher")
    if s.status != "open":
        raise HTTPException(409, "Session is finalized")
    try:
        img = engine.decode(data.image)
        faces = engine.detect(img)
    except ModelsMissing as e:
        raise HTTPException(503, str(e))
    except Exception:
        raise HTTPException(400, "Could not read image")

    if not engine.has_gallery():
        engine.load_gallery(db.query(Student).filter(Student.face_count > 0).all())

    on_roster = {st.id: st for st in roster(db, s)}
    h, w = img.shape[:2]
    now = datetime.now()
    start_dt = datetime.combine(s.date, s.start_time)
    is_late = now > start_dt + timedelta(minutes=s.late_after_min)
    results = []
    for f in sorted(faces, key=lambda r: -r[2] * r[3])[:10]:
        x, y, fw, fh = [float(v) for v in f[:4]]
        box = [max(x / w, 0), max(y / h, 0), fw / w, fh / h]
        if fw / w < settings.MIN_FACE_WIDTH_RATIO:
            results.append({"box": box, "status": "too_small", "student": None, "confidence": 0})
            continue
        pk, score = engine.best(engine.embed(img, f))
        if pk is None or score < settings.MATCH_THRESHOLD - settings.REVIEW_MARGIN:
            results.append({"box": box, "status": "unknown", "confidence": round(score, 3), "student": None})
            continue
        st = on_roster.get(pk) or db.get(Student, pk)
        info = {"id": st.id, "name": st.name, "roll_no": st.roll_no} if st else None
        if score < settings.MATCH_THRESHOLD:       # ambiguous -> teacher decides, nothing is saved
            results.append({"box": box, "status": "uncertain", "confidence": round(score, 3), "student": info})
            continue
        if pk not in on_roster:
            results.append({"box": box, "status": "not_enrolled", "confidence": round(score, 3), "student": info})
            continue
        rec = db.query(AttendanceRecord).filter_by(session_id=s.id, student_pk=pk).first()
        if rec:
            results.append({"box": box, "status": "already_marked", "confidence": round(score, 3), "student": info,
                            "value": rec.status})
            continue
        status = "Late" if is_late else "Present"
        db.add(AttendanceRecord(session_id=s.id, student_pk=pk, status=status, method="face",
                                confidence=score, time=now.time().replace(microsecond=0)))
        db.commit()
        results.append({"box": box, "status": "marked", "value": status, "confidence": round(score, 3), "student": info,
                        "time": now.strftime("%H:%M:%S")})
    return {"faces": results}
