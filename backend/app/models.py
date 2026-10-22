from datetime import datetime, date
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Date, Time, Float,
                        ForeignKey, Text, UniqueConstraint)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), default="")
    email = Column(String(120), default="")
    department = Column(String(80), default="")
    role = Column(String(20), default="student")        # admin / teacher / student
    status = Column(String(20), default="active")       # active / pending / disabled
    must_change_password = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)   # e.g. MCA
    name = Column(String(100), nullable=False)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester = Column(Integer, default=1)
    course = relationship("Course")


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    student_id = Column(String(30), unique=True, nullable=False, index=True)  # PRN
    name = Column(String(100), nullable=False)
    roll_no = Column(String(30), unique=True, nullable=False)
    course = Column(String(50), default="MCA")      # matches Course.code
    semester = Column(Integer, default=1)
    division = Column(String(10), default="A")
    email = Column(String(120), default="")
    contact = Column(String(20), default="")
    consent = Column(Boolean, default=False)
    face_reference = Column(Text, default="[]")     # JSON embeddings only, never photos
    face_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    student_pk = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    __table_args__ = (UniqueConstraint("student_pk", "subject_id", name="uq_enroll"),)


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    division = Column(String(10), default="")       # "" = all divisions
    teacher = relationship("User")
    subject = relationship("Subject")
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", "division", name="uq_assign"),)


class TimetableEntry(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    division = Column(String(10), default="")
    weekday = Column(Integer, nullable=False)       # 0=Mon .. 6=Sun
    start_time = Column(Time, nullable=False)
    duration_min = Column(Integer, default=60)
    room = Column(String(30), default="")
    subject = relationship("Subject")
    teacher = relationship("User")


class AttendanceSession(Base):
    """One lecture. Attendance is always recorded against a session."""
    __tablename__ = "attendance_sessions"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    division = Column(String(10), default="")       # "" = every enrolled student
    date = Column(Date, default=date.today, index=True)
    start_time = Column(Time, nullable=False)
    duration_min = Column(Integer, default=60)
    topic = Column(String(150), default="")
    status = Column(String(15), default="open")     # open / finalized
    late_after_min = Column(Integer, default=10)
    timetable_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)
    subject = relationship("Subject")
    teacher = relationship("User")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("subject_id", "division", "date", "start_time", name="uq_session_slot"),)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_pk = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(10), default="Present")  # Present / Absent / Late / Excused
    time = Column(Time, nullable=True)
    confidence = Column(Float, default=0.0)
    method = Column(String(12), default="face")     # face / manual / correction / finalize
    note = Column(String(255), default="")
    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student")
    __table_args__ = (UniqueConstraint("session_id", "student_pk", name="uq_record_session_student"),)


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_pk = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    requested_status = Column(String(10), default="Present")
    reason = Column(String(500), nullable=False)
    status = Column(String(10), default="pending")  # pending / approved / rejected
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decision_note = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    session = relationship("AttendanceSession")
    student = relationship("Student")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(60), default="")
    action = Column(String(60), nullable=False, index=True)
    entity = Column(String(40), default="")
    entity_id = Column(String(40), default="")
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(30), default="info")
    title = Column(String(120), nullable=False)
    body = Column(String(300), default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(50), primary_key=True)
    value = Column(String(200), default="")
