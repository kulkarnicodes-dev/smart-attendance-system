import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=120)
    student_id: str = Field(min_length=1, max_length=30)
    roll_no: str = Field(min_length=1, max_length=30)
    course: str = "MCA"
    semester: int = 1
    division: str = "A"
    consent: bool = False


class PasswordChangeIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=72)


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=72)
    full_name: str
    email: str = ""
    department: str = ""
    role: str = "teacher"


class StatusIn(BaseModel):
    status: str


class StudentIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    roll_no: str = Field(min_length=1, max_length=30)
    course: str = "MCA"
    semester: int = 1
    division: str = "A"
    email: str = ""
    contact: str = ""
    consent: bool = False


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    division: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None


class StudentOut(BaseModel):
    id: int
    student_id: str
    name: str
    roll_no: str
    course: str
    semester: int
    division: str
    email: str
    contact: str
    consent: bool
    face_count: int
    user_id: Optional[int] = None
    model_config = {"from_attributes": True}


class ImageIn(BaseModel):
    image: str


class IdentifyIn(ImageIn):
    session_id: int


class CourseIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str


class SubjectIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str
    course_id: int
    semester: int = 1


class AssignIn(BaseModel):
    teacher_id: int
    subject_id: int
    division: str = ""


class EnrollIn(BaseModel):
    subject_id: int
    student_pks: List[int] = []


class BulkEnrollIn(BaseModel):
    subject_id: int
    division: str = ""


class CsvIn(BaseModel):
    csv: str


class SettingsIn(BaseModel):
    threshold: float = Field(ge=1, le=100)
    late_after_min: int = Field(ge=0, le=120)


class TimetableIn(BaseModel):
    subject_id: int
    teacher_id: int
    division: str = ""
    weekday: int = Field(ge=0, le=6)
    start_time: str            # HH:MM
    duration_min: int = Field(default=60, ge=10, le=300)
    room: str = ""


class SessionIn(BaseModel):
    subject_id: int
    division: str = ""
    date: dt.date
    start_time: str            # HH:MM
    duration_min: int = Field(default=60, ge=10, le=300)
    topic: str = ""
    teacher_id: Optional[int] = None   # admin only


class MarkIn(BaseModel):
    student_pk: int
    status: str
    reason: str = ""


class FinalizeIn(BaseModel):
    confirm_absent: bool = False


class CorrectionIn(BaseModel):
    session_id: int
    requested_status: str = "Present"
    reason: str = Field(min_length=10, max_length=500)


class DecisionIn(BaseModel):
    approve: bool
    note: str = ""
