"""Optional demo data for your presentation:  python scripts/seed_demo.py
Creates: course MCA, 5 subjects, 2 teachers, 8 demo students (with accounts), enrollments, timetable.
Logins:  teacher1 / teacher123   teacher2 / teacher123   student1..student8 / student123
"""
import sys
from datetime import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app.models import *            # noqa
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Course).filter_by(code="MCA").first():
    print("Demo data already present."); sys.exit(0)

course = Course(code="MCA", name="Master of Computer Applications"); db.add(course); db.flush()
subs = [Subject(code=c, name=n, course_id=course.id, semester=1) for c, n in
        [("MCA101", "Python Programming"), ("MCA102", "Database Management"), ("MCA103", "Java Programming"),
         ("MCA104", "Operating Systems"), ("MCA105", "Mathematics for Computing")]]
db.add_all(subs)
teachers = []
for i, nm in enumerate(["Prof. Anita Deshmukh", "Prof. Rahul Joshi"], 1):
    t = User(username=f"teacher{i}", password_hash=hash_password("teacher123"), full_name=nm, role="teacher",
             status="active", department="MCA"); db.add(t); teachers.append(t)
db.flush()
names = ["Yash Kulkarni", "Rahul Patil", "Amit Sharma", "Sneha Pawar", "Priya Joshi", "Rohit More", "Neha Kale", "Sagar Shinde"]
for i, nm in enumerate(names, 1):
    u = User(username=f"student{i}", password_hash=hash_password("student123"), full_name=nm, role="student",
             status="active", email=f"student{i}@example.com"); db.add(u); db.flush()
    st = Student(user_id=u.id, student_id=f"PRN2026{i:03d}", name=nm, roll_no=f"MCA{i:03d}", course="MCA", semester=1,
                 division="A", email=u.email, consent=True); db.add(st); db.flush()
    for s in subs:
        db.add(Enrollment(student_pk=st.id, subject_id=s.id))
for i, s in enumerate(subs):
    db.add(TeacherAssignment(teacher_id=teachers[i % 2].id, subject_id=s.id, division=""))
    for wd in (i % 5, (i + 2) % 5):
        db.add(TimetableEntry(subject_id=s.id, teacher_id=teachers[i % 2].id, division="A", weekday=wd,
                              start_time=time(9 + i % 4 * 1, 0) if wd == i % 5 else time(14, 0), duration_min=60, room=f"R{101 + i}"))
db.commit()
print("Demo data created. Teachers: teacher1/teacher123, teacher2/teacher123. Students: student1..8 / student123")
