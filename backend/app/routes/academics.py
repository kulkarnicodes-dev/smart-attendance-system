import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Course, Subject, TeacherAssignment, Enrollment, Student, User
from ..schemas import CourseIn, SubjectIn, AssignIn, EnrollIn, BulkEnrollIn, CsvIn
from ..security import require_roles, get_current_user
from ..services import audit

router = APIRouter(prefix="/api/academics", tags=["academics"])
admin = Depends(require_roles("admin"))
staff = Depends(require_roles("admin", "teacher"))


@router.get("/courses")
def courses(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{"id": c.id, "code": c.code, "name": c.name} for c in db.query(Course).order_by(Course.code)]


@router.post("/courses", status_code=201)
def add_course(d: CourseIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(Course).filter_by(code=d.code).first():
        raise HTTPException(409, "Course code already exists")
    c = Course(code=d.code, name=d.name)
    db.add(c)
    audit(db, a, "course.create", "course", d.code)
    db.commit()
    return {"id": c.id, "code": c.code, "name": c.name}


@router.delete("/courses/{cid}")
def del_course(cid: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    c = db.get(Course, cid)
    if not c:
        raise HTTPException(404, "Not found")
    if db.query(Subject).filter_by(course_id=cid).first():
        raise HTTPException(409, "Delete this course's subjects first")
    db.delete(c)
    audit(db, a, "course.delete", "course", cid)
    db.commit()
    return {"ok": True}


def _sub(s: Subject):
    return {"id": s.id, "code": s.code, "name": s.name, "semester": s.semester, "course_id": s.course_id,
            "course": s.course.code if s.course else ""}


@router.get("/subjects")
def subjects(course_id: Optional[int] = None, semester: Optional[int] = None,
             _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Subject)
    if course_id:
        q = q.filter(Subject.course_id == course_id)
    if semester:
        q = q.filter(Subject.semester == semester)
    return [_sub(s) for s in q.order_by(Subject.semester, Subject.code)]


@router.post("/subjects", status_code=201)
def add_subject(d: SubjectIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(Subject).filter_by(code=d.code).first():
        raise HTTPException(409, "Subject code already exists")
    if not db.get(Course, d.course_id):
        raise HTTPException(400, "Course not found")
    s = Subject(**d.model_dump())
    db.add(s)
    audit(db, a, "subject.create", "subject", d.code)
    db.commit()
    db.refresh(s)
    return _sub(s)


@router.delete("/subjects/{sid}")
def del_subject(sid: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    s = db.get(Subject, sid)
    if not s:
        raise HTTPException(404, "Not found")
    from ..models import AttendanceSession
    if db.query(AttendanceSession).filter_by(subject_id=sid).first():
        raise HTTPException(409, "This subject has lecture sessions and cannot be deleted")
    db.delete(s)
    audit(db, a, "subject.delete", "subject", sid)
    db.commit()
    return {"ok": True}


# ---- teacher assignments ----
def _assign(t: TeacherAssignment):
    return {"id": t.id, "teacher_id": t.teacher_id, "teacher": t.teacher.full_name or t.teacher.username,
            "subject_id": t.subject_id, "subject": t.subject.name, "code": t.subject.code, "division": t.division}


@router.get("/assignments")
def assignments(user: User = Depends(require_roles("admin", "teacher")), db: Session = Depends(get_db)):
    q = db.query(TeacherAssignment)
    if user.role == "teacher":
        q = q.filter(TeacherAssignment.teacher_id == user.id)
    return [_assign(t) for t in q.all()]


@router.post("/assignments", status_code=201)
def add_assignment(d: AssignIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    t = db.get(User, d.teacher_id)
    if not t or t.role != "teacher":
        raise HTTPException(400, "Selected user is not a teacher")
    if not db.get(Subject, d.subject_id):
        raise HTTPException(400, "Subject not found")
    if db.query(TeacherAssignment).filter_by(teacher_id=d.teacher_id, subject_id=d.subject_id, division=d.division).first():
        raise HTTPException(409, "Already assigned")
    row = TeacherAssignment(**d.model_dump())
    db.add(row)
    audit(db, a, "assignment.create", "subject", d.subject_id, f"teacher={d.teacher_id} division={d.division or 'all'}")
    db.commit()
    return _assign(row)


@router.delete("/assignments/{aid}")
def del_assignment(aid: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(TeacherAssignment, aid)
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row)
    audit(db, a, "assignment.delete", "assignment", aid)
    db.commit()
    return {"ok": True}


# ---- enrollments ----
@router.get("/enrollments", dependencies=[staff])
def enrolled(subject_id: int, db: Session = Depends(get_db)):
    rows = (db.query(Student).join(Enrollment, Enrollment.student_pk == Student.id)
            .filter(Enrollment.subject_id == subject_id).order_by(Student.roll_no).all())
    return [{"id": s.id, "roll_no": s.roll_no, "name": s.name, "division": s.division} for s in rows]


@router.post("/enrollments")
def enroll(d: EnrollIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    added = 0
    for pk in d.student_pks:
        if db.get(Student, pk) and not db.query(Enrollment).filter_by(student_pk=pk, subject_id=d.subject_id).first():
            db.add(Enrollment(student_pk=pk, subject_id=d.subject_id))
            added += 1
    audit(db, a, "enrollment.add", "subject", d.subject_id, f"{added} students")
    db.commit()
    return {"added": added}


@router.post("/enrollments/bulk")
def enroll_bulk(d: BulkEnrollIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Enroll every student of the subject's course + semester (optionally one division)."""
    sub = db.get(Subject, d.subject_id)
    if not sub:
        raise HTTPException(404, "Subject not found")
    q = db.query(Student).filter(Student.course == sub.course.code, Student.semester == sub.semester)
    if d.division:
        q = q.filter(Student.division == d.division)
    added = 0
    for s in q.all():
        if not db.query(Enrollment).filter_by(student_pk=s.id, subject_id=sub.id).first():
            db.add(Enrollment(student_pk=s.id, subject_id=sub.id))
            added += 1
    audit(db, a, "enrollment.bulk", "subject", sub.id, f"{added} students")
    db.commit()
    return {"added": added}


@router.delete("/enrollments")
def unenroll(subject_id: int, student_pk: int, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.query(Enrollment).filter_by(subject_id=subject_id, student_pk=student_pk).first()
    if row:
        db.delete(row)
        audit(db, a, "enrollment.remove", "subject", subject_id, f"student={student_pk}")
        db.commit()
    return {"ok": True}


# ---- CSV import ----
@router.post("/import-students")
def import_students(d: CsvIn, a: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Columns: student_id,name,roll_no,course,semester,division,email  (header row required).
    Imported students register later with the same student ID + roll no, and are auto-approved if the email matches."""
    reader = csv.DictReader(io.StringIO(d.csv.strip()))
    need = {"student_id", "name", "roll_no"}
    if not reader.fieldnames or not need.issubset({h.strip() for h in reader.fieldnames}):
        raise HTTPException(400, "CSV needs at least the columns: student_id, name, roll_no")
    added, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, start=2):
        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        if not (row.get("student_id") and row.get("name") and row.get("roll_no")):
            errors.append(f"line {i}: missing required value"); continue
        if db.query(Student).filter((Student.student_id == row["student_id"]) | (Student.roll_no == row["roll_no"])).first():
            skipped += 1; continue
        try:
            sem = int(row.get("semester") or 1)
        except ValueError:
            errors.append(f"line {i}: semester must be a number"); continue
        db.add(Student(student_id=row["student_id"], name=row["name"], roll_no=row["roll_no"],
                       course=row.get("course") or "MCA", semester=sem, division=row.get("division") or "A",
                       email=row.get("email", "")))
        added += 1
    audit(db, a, "students.import", "students", "", f"added={added} skipped={skipped} errors={len(errors)}")
    db.commit()
    return {"added": added, "skipped_existing": skipped, "errors": errors[:20]}
