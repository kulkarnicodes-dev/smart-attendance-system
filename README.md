# Smart Attendance Management System
### MCA First-Year Mini Project | Campus Edition

An AI-powered Smart Attendance Management System developed to automate college attendance using face recognition, lecture-wise sessions, and role-based management.

<p align="center">
  <a href="https://smart-attendance-system-neon.vercel.app/">🌐 Live Project Demo</a> ·
  <a href="https://smart-attendance-system-3pts.onrender.com/">⚙️ Backend API</a> ·
  <a href="https://smart-attendance-system-3pts.onrender.com/docs">📚 API Documentation</a>
</p>

---

## 🎓 Academic Project Details

| Detail | Information |
|---|---|
| Project Title | Smart Attendance Management System |
| Project Type | MCA First-Year Mini Project |
| College Name | Zeal Institute of Business Administration, Computer Application and Research (ZIBACAR) |
| Course | Master of Computer Applications (MCA) |
| Project Domain | Artificial Intelligence and Web Development |
| Project Category | Full-Stack Application |

### 👨‍🎓 Project Team

| Student Name | Roll Number |
|---|---|
| Yash Kulkarni | MC2628140 |
| Aaryan Koshti | MC2628137 |

### 👩‍🏫 Project Mentor

**Madhuvi Shamkuwar**

---

## 🚀 Live Deployment

| Component | Platform | Link |
|---|---|---|
| Frontend Application | Vercel | https://smart-attendance-system-neon.vercel.app/ |
| Backend API | Render | https://smart-attendance-system-3pts.onrender.com/ |
| API Documentation | FastAPI | https://smart-attendance-system-3pts.onrender.com/docs |
| Health Check | FastAPI | https://smart-attendance-system-3pts.onrender.com/api/health |

**Deployment note:** The backend currently uses temporary SQLite storage on Render's free plan. Database records may be lost when the service restarts or redeploys. This deployment is intended for testing and demonstration, not permanent attendance records.

## 📌 Project Overview

The Smart Attendance Management System is designed to simplify and automate attendance management in colleges and educational institutions.

The system uses face recognition to identify students and record lecture-wise attendance. It provides separate portals for Admin, Teachers, and Students.

### Key Features

- Admin, Teacher, and Student roles
- Face recognition-based attendance
- Lecture-wise attendance sessions
- Student and teacher management
- Course and subject management
- Timetable management
- Attendance analytics and reports
- Attendance correction requests
- Audit logs and notifications
- CSV import and export
- Secure authentication using JWT

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Tailwind CSS, Recharts |
| Backend | Python, FastAPI |
| Database | SQLite / MySQL |
| ORM | SQLAlchemy |
| Authentication | JWT, bcrypt |
| Face Detection | OpenCV YuNet |
| Face Recognition | OpenCV SFace |
| Deployment | Vercel, Render |

**Privacy:** The system stores face embeddings rather than raw face photographs.

## 👥 User Roles

### 1. Admin
- Manage teacher and student accounts.
- Approve student registrations.
- Manage courses, subjects, and enrollments.
- Assign teachers to subjects.
- Import student records using CSV.
- Create and manage timetables.
- Configure attendance rules.
- View reports and audit logs.
- Manage correction requests.

### 2. Teacher
- View daily timetable.
- Start lecture-wise attendance sessions.
- Capture attendance using face recognition.
- Manually mark attendance when required.
- Review uncertain face matches.
- Finalize and lock attendance sessions.
- Approve or reject correction requests.

### 3. Student
- Register an account.
- Register personal face data.
- View attendance percentage.
- Check subject-wise attendance.
- View attendance history and timetable.
- Receive low-attendance alerts.
- Download attendance reports.
- Submit attendance correction requests.

## 🧠 Face Recognition Workflow

1. Camera captures the student's face.
2. OpenCV YuNet detects the face.
3. OpenCV SFace generates a face embedding.
4. The embedding is compared with registered face embeddings.
5. Cosine similarity is used for matching.
6. Uncertain matches are sent for teacher review.
7. Confirmed attendance is saved against the active lecture session.

## 🔐 Security and Attendance Rules

- Every endpoint validates user roles on the backend.
- Students cannot access another student's records by changing an ID.
- Teachers can manage only their assigned subjects and sessions.
- One attendance record is allowed per student per session.
- Only enrolled students can be marked present.
- Uncertain face matches are not automatically saved.
- Changes after finalization require a reason and are audit-logged.
- Passwords are hashed using bcrypt.
- Login is locked after five incorrect password attempts.

### Attendance Calculation

`(Present + Late) / (Present + Late + Absent) × 100`

Only finalized sessions are included. Excused attendance is excluded.

## 💻 Local Installation

### Prerequisites
- Python 3.11
- Node.js and npm
- Git
- VS Code

### 1. Clone Repository

```bash
git clone https://github.com/kulkarnicodes-dev/smart-attendance-system.git
cd smart-attendance-system
```

### 2. Backend Setup

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` using `.env.example` and configure the environment variables.

Ensure these model files exist in `backend/models/`:

```text
face_detection_yunet_2023mar.onnx
face_recognition_sface_2021dec.onnx
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal:

```cmd
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## 🌱 Optional Demo Data

```cmd
cd backend
python scripts\seed_demo.py
```

Sample local demo accounts:

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Teacher | teacher1 | teacher123 |
| Teacher | teacher2 | teacher123 |
| Student | student1 | student123 |
| Student | student2 | student123 |

Additional student accounts are available through `student8`.

These are local demo credentials generated by the seed script. They are not guaranteed to exist in the deployed application. Never use default credentials for a public production deployment.

## 🎯 Suggested Project Demonstration

1. Admin creates courses and subjects.
2. Admin assigns teachers to subjects.
3. Admin enrolls students into classes.
4. Students register and wait for approval.
5. Students register face data using approximately 20 samples.
6. Teacher starts a lecture attendance session.
7. Teacher starts face recognition attendance.
8. Teacher reviews uncertain matches and finalizes attendance.
9. Students view attendance percentage and history.
10. Students submit correction requests.
11. Teacher reviews correction requests.
12. Admin checks the audit log.

## 📂 Project Structure

```text
smart-attendance-system/
│
├── backend/
│   ├── app/
│   ├── models/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
│
├── database/
├── docs/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── PROGRESS.md
```

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| Teacher cannot select a subject | Assign the teacher to the subject from Admin → Academics. |
| Student roster is empty | Enroll the class from Admin → Academics → Enrollment. |
| Account awaiting approval | Admin must approve the student account. |
| Face recognition not working | Verify ONNX model files exist in `backend/models/`. |
| Incorrect face match | Review `MATCH_THRESHOLD` and `REVIEW_MARGIN`. |
| Forgot password | Admin can reset the user's password. |
| Backend unavailable | Check Render service status and backend logs. |
| Frontend cannot connect | Verify API URL and CORS configuration. |

## 🔮 Future Enhancements

- Permanent cloud database integration.
- Advanced attendance analytics.
- Mobile-friendly portals.
- Email and SMS notifications.
- Improved face recognition performance.
- Automated cloud database backups.
- Additional reporting and export options.

---

## 👨‍💻 Project Credits

**Project Title:** Smart Attendance Management System

**Developed by:**
- Yash Kulkarni — MC2628140
- Aaryan Koshti — MC2628137

**Project Mentor:** Madhuvi Shamkuwar

**College:** Zeal Institute of Business Administration, Computer Application and Research (ZIBACAR)

**Programme:** Master of Computer Applications (MCA)

**Project Type:** MCA First-Year Mini Project

**GitHub Repository:** https://github.com/kulkarnicodes-dev/smart-attendance-system

---

<p align="center">
  <strong>Smart Attendance Management System</strong><br/>
  <em>An MCA Mini Project — Making Campus Attendance Smarter with AI.</em>
</p>
