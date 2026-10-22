"""One-time upgrade of the v1 database (users / students / attendance) to the v2 role + session schema.

Safe to call on every start: it does nothing unless the old `attendance` table is found.
SQLite files are backed up first.
"""
import shutil
from datetime import datetime, time as dtime
from sqlalchemy import inspect, text

from .config import settings, BASE_DIR


def _backup_sqlite():
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        from pathlib import Path
        p = Path(path)
        if not p.is_absolute():
            p = BASE_DIR / p
        if p.exists():
            dest = p.with_name(f"{p.stem}.v1-backup-{datetime.now():%Y%m%d-%H%M%S}{p.suffix}")
            shutil.copy2(p, dest)
            print(f"[migrate] backup written: {dest.name}")


def _rows(conn, table):
    return [dict(r._mapping) for r in conn.execute(text(f"SELECT * FROM {table}"))]


def read_and_drop_legacy(engine):
    """Return legacy data (or None) and drop the old tables so the new ones can be created."""
    insp = inspect(engine)
    if not insp.has_table("attendance"):
        return None
    if "session_id" in {c["name"] for c in insp.get_columns("attendance")}:
        return None  # already v2
    _backup_sqlite()
    with engine.begin() as conn:
        legacy = {t: _rows(conn, t) for t in ("users", "students", "attendance") if insp.has_table(t)}
        for t in ("attendance", "students", "users"):
            if insp.has_table(t):
                conn.execute(text(f"DROP TABLE {t}"))
    print(f"[migrate] v1 data read: {len(legacy.get('users', []))} users, "
          f"{len(legacy.get('students', []))} students, {len(legacy.get('attendance', []))} attendance rows")
    return legacy


def restore_legacy(db, legacy):
    from .models import User, Student, Course, Subject, Enrollment, AttendanceSession, AttendanceRecord
    old_to_new_user, old_to_new_student = {}, {}
    admin = None
    for u in legacy.get("users", []):
        role = u.get("role") if u.get("role") in ("admin", "teacher") else "teacher"
        nu = User(username=u["username"], password_hash=u["password_hash"], full_name=u.get("full_name") or "",
                  role=role, status="active")
        db.add(nu)
        db.flush()
        old_to_new_user[u["id"]] = nu.id
        if role == "admin" and admin is None:
            admin = nu
    for s in legacy.get("students", []):
        ns = Student(student_id=s["student_id"], name=s["name"], roll_no=s["roll_no"], course=s.get("course") or "MCA",
                     division=s.get("division") or "A", semester=1, email=s.get("email") or "",
                     contact=s.get("contact") or "", consent=bool(s.get("consent")),
                     face_reference=s.get("face_reference") or "[]", face_count=s.get("face_count") or 0)
        db.add(ns)
        db.flush()
        old_to_new_student[s["id"]] = ns.id

    att = legacy.get("attendance", [])
    if att and admin:
        course = db.query(Course).filter_by(code="MCA").first() or Course(code="MCA", name="Master of Computer Applications")
        db.add(course)
        db.flush()
        subject = Subject(code="GEN", name="General (migrated v1 attendance)", course_id=course.id, semester=1)
        db.add(subject)
        db.flush()
        for pk in old_to_new_student.values():
            db.add(Enrollment(student_pk=pk, subject_id=subject.id))
        groups = {}
        for a in att:
            groups.setdefault((str(a["date"]), a.get("session") or "General"), []).append(a)
        for i, ((d, label), rows) in enumerate(sorted(groups.items())):
            first_time = rows[0].get("time")
            try:
                start = datetime.strptime(str(first_time)[:8], "%H:%M:%S").time()
            except Exception:
                start = dtime(9, 0)
            # unique slot: nudge start by `i` minutes if two groups share a day
            start = dtime(start.hour, (start.minute + i % 30) % 60)
            sess = AttendanceSession(subject_id=subject.id, teacher_id=admin.id, division="",
                                     date=datetime.strptime(d[:10], "%Y-%m-%d").date(), start_time=start,
                                     topic=f"Migrated: {label}", status="finalized", finalized_at=datetime.utcnow())
            db.add(sess)
            db.flush()
            seen = set()
            for a in rows:
                pk = old_to_new_student.get(a["student_pk"])
                if pk is None or pk in seen:
                    continue
                seen.add(pk)
                db.add(AttendanceRecord(session_id=sess.id, student_pk=pk, status=a.get("status") or "Present",
                                        confidence=a.get("confidence") or 0, method=a.get("method") or "face"))
            for pk in old_to_new_student.values():  # finalized sessions have a record for every student
                if pk not in seen:
                    db.add(AttendanceRecord(session_id=sess.id, student_pk=pk, status="Absent", method="finalize"))
    db.commit()
    print("[migrate] v1 -> v2 migration complete")
