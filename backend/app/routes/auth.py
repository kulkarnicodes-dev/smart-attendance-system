from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models import User, Student
from ..schemas import LoginIn, PasswordChangeIn, RegisterIn
from ..security import verify_password, create_token, get_current_user, hash_password, rate_limit
from ..services import audit, notify

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(u: User):
    return {"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role,
            "must_change_password": bool(u.must_change_password)}


@router.post("/login")
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, "login", 30, 300)
    user = db.query(User).filter(User.username == data.username.strip()).first()
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(429, "Account temporarily locked after too many failed attempts. Try again later.")
    if not user or not verify_password(data.password, user.password_hash):
        if user:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
                user.failed_attempts = 0
                audit(db, user, "auth.locked", "user", user.id, "Too many failed logins")
            db.commit()
        raise HTTPException(401, "Invalid username or password")
    if user.status == "pending":
        raise HTTPException(403, "Your account is awaiting admin approval.")
    if user.status != "active":
        raise HTTPException(403, "This account has been disabled. Contact the administrator.")
    user.failed_attempts, user.locked_until, user.last_login = 0, None, datetime.utcnow()
    db.commit()
    return {"access_token": create_token(user.username), "token_type": "bearer", "user": _user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/register", status_code=201)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    """Student self-registration. Account stays 'pending' until an admin approves it,
    unless the admin pre-imported this student with the same email (then it is auto-approved)."""
    rate_limit(request, "register", 10, 3600)
    if not data.consent:
        raise HTTPException(400, "Consent for face-data processing is required to register")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(409, "Username already taken")
    student = db.query(Student).filter(Student.student_id == data.student_id).first()
    approved = False
    if student:
        if student.user_id:
            raise HTTPException(409, "This student ID already has an account")
        if student.roll_no != data.roll_no:
            raise HTTPException(400, "Student ID and roll number do not match our records")
        approved = bool(student.email) and student.email.lower() == data.email.lower()
    else:
        if db.query(Student).filter(Student.roll_no == data.roll_no).first():
            raise HTTPException(409, "Roll number already exists")
        student = Student(student_id=data.student_id, name=data.full_name, roll_no=data.roll_no, course=data.course,
                          semester=data.semester, division=data.division, email=data.email)
        db.add(student)
    user = User(username=data.username, password_hash=hash_password(data.password), full_name=data.full_name,
                email=data.email, role="student", status="active" if approved else "pending")
    db.add(user)
    db.flush()
    student.user_id = user.id
    student.consent = True
    audit(db, user, "user.register", "user", user.id, f"student_id={data.student_id} auto_approved={approved}")
    for admin in db.query(User).filter(User.role == "admin", User.status == "active").all():
        notify(db, admin.id, "New student registration", f"{data.full_name} ({data.roll_no}) is waiting for approval.", "approval")
    db.commit()
    return {"message": "Account activated. You can sign in now." if approved
            else "Registration received. An administrator must approve your account before you can sign in.",
            "approved": approved}


@router.post("/change-password")
def change_password(data: PasswordChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Old password is incorrect")
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    audit(db, user, "auth.password_change", "user", user.id)
    db.commit()
    return {"message": "Password updated"}
