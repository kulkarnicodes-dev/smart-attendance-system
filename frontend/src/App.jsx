import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Students from './pages/Students.jsx'
import StudentForm from './pages/StudentForm.jsx'
import FaceCapture from './pages/FaceCapture.jsx'
import Sessions from './pages/Sessions.jsx'
import SessionRoom from './pages/SessionRoom.jsx'
import MyAttendance from './pages/MyAttendance.jsx'
import Corrections from './pages/Corrections.jsx'
import Timetable from './pages/Timetable.jsx'
import Academics from './pages/Academics.jsx'
import Users from './pages/Users.jsx'
import Audit from './pages/Audit.jsx'
import Reports from './pages/Reports.jsx'
import Notifications from './pages/Notifications.jsx'
import Settings from './pages/Settings.jsx'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-10 text-ink-mute">Loading…</div>
  return user ? children : <Navigate to="/login" replace />
}

// frontend guard is only for UX - the backend enforces every permission itself
function Role({ allow, children }) {
  const { user } = useAuth()
  return allow.includes(user.role) ? children : <Navigate to="/" replace />
}

const staff = ['admin', 'teacher']

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/students" element={<Role allow={staff}><Students /></Role>} />
        <Route path="/students/new" element={<Role allow={['admin']}><StudentForm /></Role>} />
        <Route path="/students/:id/face" element={<Role allow={staff}><FaceCapture /></Role>} />
        <Route path="/my-face" element={<Role allow={['student']}><FaceCapture /></Role>} />
        <Route path="/sessions" element={<Role allow={staff}><Sessions /></Role>} />
        <Route path="/sessions/:id" element={<Role allow={staff}><SessionRoom /></Role>} />
        <Route path="/my-attendance" element={<Role allow={['student']}><MyAttendance /></Role>} />
        <Route path="/corrections" element={<Corrections />} />
        <Route path="/timetable" element={<Timetable />} />
        <Route path="/academics" element={<Role allow={['admin']}><Academics /></Role>} />
        <Route path="/users" element={<Role allow={['admin']}><Users /></Role>} />
        <Route path="/audit" element={<Role allow={['admin']}><Audit /></Role>} />
        <Route path="/reports" element={<Role allow={staff}><Reports /></Role>} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
