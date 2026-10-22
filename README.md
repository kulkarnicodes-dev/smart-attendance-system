# Smart Attendance Management System v2 (Campus edition)

Roles: **Admin / Teacher / Student**  |  Lecture-wise sessions  |  Face recognition  |  Timetable  |  Analytics  |
Correction requests  |  Audit log  |  Notifications

Stack: React + Tailwind + Recharts, FastAPI + SQLAlchemy, OpenCV (YuNet + SFace), SQLite (or MySQL), JWT.
**No new Python or npm packages were added in v2.**

## 1. Upgrading your running v1 project (keeps your data)

1. Close both terminals (backend + frontend).
2. Extract this zip **over your existing `smart-attendance` folder** (say "replace" for files). Your `backend/.env`,
   `backend/models/*.onnx` and `backend/attendance.db` are not in the zip, so they stay untouched.
3. Start the backend as before. On first start it detects the old database, writes a backup copy
   (`attendance.v1-backup-<time>.db`) and migrates it automatically:
   - old users stay (admin keeps the same password), students and **face data are preserved**,
   - old attendance becomes finalized "General (migrated v1 attendance)" lecture sessions.
4. `cd frontend && npm run dev` (run `npm install` only if it complains).

## 2. Run commands (CMD)

```cmd
:: Terminal 1 - backend
cd smart-attendance\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

:: Terminal 2 - frontend
cd smart-attendance\frontend
npm run dev
```
Open http://localhost:5173  (API docs: http://127.0.0.1:8000/docs).
Fresh install: see the commands in `backend/run.bat` (venv, pip install, copy .env.example .env, download models).

Optional demo data for your presentation (2 teachers, 8 students, 5 subjects, timetable):
```cmd
cd smart-attendance\backend
python scripts\seed_demo.py
```
Logins: `admin / admin123`, `teacher1 / teacher123`, `teacher2 / teacher123`, `student1..student8 / student123`.

## 3. How each role works

**Admin** - Users (approve students, create teachers, disable, reset password) - Academics (courses, subjects,
teacher assignments, enrollments, CSV import) - Timetable (conflicts blocked) - Attendance rules (minimum %, late after N min)
- Reports - Corrections - Audit log.

**Teacher** - Dashboard shows today's timetable; **Start session** creates the lecture and opens the session room.
In the room: *Start face attendance* (camera), manual mark with dropdown, review of uncertain matches,
**Finalize & lock**. Unmarked students become Absent only after the teacher confirms.

**Student** - Registers (admin approves), registers own face, sees overall and subject-wise %, history, timetable,
low-attendance alerts ("attend N more lectures"), downloads CSV, submits correction requests.

## 4. Suggested end-to-end demo

1. Admin: Academics -> add course/subjects -> Teacher assignments -> Enrollment -> *Enroll class*.
2. Student: Register -> Admin approves in Users -> student logs in -> *My face data* -> capture 20 samples.
3. Teacher: Dashboard -> Start session -> Start face attendance -> Finalize.
4. Student: sees attendance and a notification if absent -> *Request correction* -> Teacher approves.
5. Admin: Audit log shows every change.

## 5. Rules built into the backend (not just the UI)

- Every endpoint checks the role server-side; a student cannot read another student's data by changing an ID.
- Teachers only see/manage their own sessions and assigned subjects.
- One record per student per session (database unique constraint).
- Only students enrolled in the subject (and division) can be marked; others show "Not enrolled".
- Matches slightly below the threshold are **not saved**; the teacher confirms them.
- Late = marked after `late_after_min`. Percentage = (Present+Late) / (Present+Late+Absent) over **finalized** sessions;
  Excused is excluded.
- Changes after finalizing need a reason and are audit-logged. Face embeddings only - no photos stored.
- Login lock after 5 wrong passwords; passwords hashed with bcrypt.

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| Teacher cannot pick a subject when creating a session | Admin must assign the teacher to that subject (Academics -> Teacher assignments) |
| Roster is empty | Admin: Academics -> Enrollment -> *Enroll class* (student course/semester must match the subject's) |
| "Account awaiting approval" | Admin: Users -> Approve |
| Wrong person matched / real student unknown | tune `MATCH_THRESHOLD` / `REVIEW_MARGIN` in `backend/.env` |
| Forgot password | Admin: Users -> Reset password (temporary password, forced change) |
| Backup | `python scripts\backup_db.py` (SQLite) |
