# Build progress (resume point)

## v1 (done): single-teacher face attendance
## v2 (done): campus edition
- [x] Roles + approval + lockout + audit log
- [x] Courses, subjects, enrollments, teacher assignments, CSV import
- [x] Timetable with conflict detection, start-session-from-timetable
- [x] Lecture sessions (open/finalized), per-session records, late/excused, confirm-before-absent
- [x] Face recognition tied to sessions (roster check, uncertain-match review, duplicate-face rejection)
- [x] Student portal (percentages, history, alerts, corrections), Teacher portal, Admin portal
- [x] Analytics (threshold, lectures-to-recover, per subject/division/month), CSV exports
- [x] In-app notifications, v1 -> v2 automatic data migration, backup script

## Not built yet (next candidates)
- [ ] PDF export (needs a new dependency, e.g. reportlab)
- [ ] QR-code fallback attendance
- [ ] Liveness / anti-spoof check
- [ ] Email notifications and self-service "forgot password" by email
- [ ] Holiday/cancellation management, exam-eligibility report, Docker
- [ ] Automated tests (pytest) - the v2 code has been syntax/static-checked but not run end-to-end

To continue in a new chat: upload this zip and say "continue from PROGRESS.md".
