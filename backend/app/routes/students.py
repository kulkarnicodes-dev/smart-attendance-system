import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..face_service import engine, ModelsMissing
from ..models import Student, User
from ..schemas import StudentIn, StudentOut, StudentUpdate, ImageIn
from ..security import get_current_user, require_roles
from ..services import audit, own_student

router = APIRouter(prefix="/api/students", tags=["students"])
staff = Depends(require_roles("admin", "teacher"))


def _get(db: Session, pk: int) -> Student:
    s = db.get(Student, pk)
    if not s:
        raise HTTPException(404, "Student not found")
    return s


def _can_touch(user: User, s: Student, db: Session):
    if user.role in ("admin", "teacher") or s.user_id == user.id:
        return
    raise HTTPException(403, "You can only manage your own face data")


@router.get("/me", response_model=StudentOut)
def my_record(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    s = own_student(db, user)
    if not s:
        raise HTTPException(404, "No student profile linked to this account")
    return s


@router.get("", response_model=List[StudentOut], dependencies=[staff])
def list_students(q: Optional[str] = None, division: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Student)
    if q:
        like = f"%{q}%"
        query = query.filter(Student.name.like(like) | Student.roll_no.like(like) | Student.student_id.like(like))
    if division:
        query = query.filter(Student.division == division)
    return query.order_by(Student.roll_no).all()


@router.post("", response_model=StudentOut, status_code=201)
def create_student(data: StudentIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if not data.consent:
        raise HTTPException(400, "Student's consent for biometric data is required")
    if db.query(Student).filter((Student.student_id == data.student_id) | (Student.roll_no == data.roll_no)).first():
        raise HTTPException(409, "Student ID or Roll No already exists")
    s = Student(**data.model_dump())
    db.add(s)
    db.flush()
    audit(db, a, "student.create", "student", s.id, s.roll_no)
    db.commit()
    db.refresh(s)
    return s


@router.get("/{pk}", response_model=StudentOut)
def get_student(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _get(db, pk)
    _can_touch(user, s, db)
    return s


@router.put("/{pk}", response_model=StudentOut)
def update_student(pk: int, data: StudentUpdate, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    s = _get(db, pk)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    audit(db, a, "student.update", "student", pk)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{pk}")
def delete_student(pk: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    s = _get(db, pk)
    audit(db, a, "student.delete", "student", pk, f"{s.roll_no} incl. biometric data and attendance")
    db.delete(s)
    db.commit()
    engine.invalidate()
    return {"message": "Student and all biometric data deleted"}


@router.post("/{pk}/face")
def add_face_sample(pk: int, data: ImageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """ONE webcam frame -> embedding. The image is discarded. Rejects a face already enrolled for someone else."""
    s = _get(db, pk)
    _can_touch(user, s, db)
    if not s.consent:
        raise HTTPException(400, "No biometric consent recorded for this student")
    try:
        img = engine.decode(data.image)
        faces = engine.detect(img)
    except ModelsMissing as e:
        raise HTTPException(503, str(e))
    except Exception:
        raise HTTPException(400, "Could not read image")
    if len(faces) == 0:
        raise HTTPException(422, "No face detected - face the camera in good light")
    if len(faces) > 1:
        raise HTTPException(422, "Multiple faces detected - only one person at a time")
    if faces[0][2] / img.shape[1] < 0.18:
        raise HTTPException(422, "Move closer to the camera")
    emb = engine.embed(img, faces[0])

    engine.load_gallery(db.query(Student).filter(Student.face_count > 0).all())
    other, score = engine.best(emb, exclude=s.id)
    if other is not None and score >= settings.DUPLICATE_FACE_THRESHOLD:
        raise HTTPException(409, "This face already looks like another registered student. Ask an admin to check.")

    embs = json.loads(s.face_reference or "[]")
    if len(embs) >= settings.MAX_FACE_SAMPLES:
        raise HTTPException(409, f"Maximum {settings.MAX_FACE_SAMPLES} samples reached")
    embs.append([round(float(x), 6) for x in emb])
    s.face_reference = json.dumps(embs)
    s.face_count = len(embs)
    db.commit()
    engine.invalidate()
    return {"face_count": s.face_count}


@router.delete("/{pk}/face")
def reset_faces(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _get(db, pk)
    _can_touch(user, s, db)
    s.face_reference, s.face_count = "[]", 0
    audit(db, user, "biometric.delete", "student", pk, "face samples removed")
    db.commit()
    engine.invalidate()
    return {"face_count": 0}
