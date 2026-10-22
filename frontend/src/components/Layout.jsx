import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, ScanFace, ClipboardList, BarChart3, Settings, LogOut, CalendarDays, BookOpen,
  ShieldCheck, ScrollText, Bell, MessageSquareWarning, UserCog } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../auth.jsx'

const NAV = {
  admin: [
    ['/', 'Dashboard', LayoutDashboard, true], ['/sessions', 'Lecture sessions', ClipboardList], ['/students', 'Students', Users],
    ['/academics', 'Academics', BookOpen], ['/timetable', 'Timetable', CalendarDays], ['/users', 'Users', UserCog],
    ['/corrections', 'Corrections', MessageSquareWarning], ['/reports', 'Reports', BarChart3], ['/audit', 'Audit log', ScrollText],
  ],
  teacher: [
    ['/', 'Dashboard', LayoutDashboard, true], ['/sessions', 'Lecture sessions', ClipboardList], ['/timetable', 'Timetable', CalendarDays],
    ['/corrections', 'Corrections', MessageSquareWarning], ['/reports', 'Reports', BarChart3], ['/students', 'Students', Users],
  ],
  student: [
    ['/', 'Dashboard', LayoutDashboard, true], ['/my-attendance', 'My attendance', ClipboardList], ['/timetable', 'Timetable', CalendarDays],
    ['/corrections', 'Corrections', MessageSquareWarning], ['/my-face', 'My face data', ScanFace],
  ],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    const load = () => api('/api/notifications').then((r) => setUnread(r.unread)).catch(() => {})
    load()
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [])

  const items = [...(NAV[user.role] || []), ['/notifications', 'Notifications', Bell], ['/settings', 'Settings', Settings]]
  const link = ({ isActive }) =>
    `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'bg-white/10 text-white' : 'text-white/70 hover:bg-white/5 hover:text-white'}`

  return (
    <div className="min-h-screen md:flex">
      <aside className="bg-ink text-white md:w-60 md:min-h-screen md:sticky md:top-0 md:h-screen flex md:flex-col">
        <div className="hidden md:block px-5 py-6">
          <div className="text-lg font-bold leading-tight">Smart Attendance</div>
          <div className="mt-1 inline-flex items-center gap-1 rounded bg-white/10 px-2 py-0.5 text-xs capitalize"><ShieldCheck size={12} /> {user.role} portal</div>
        </div>
        <nav className="flex md:flex-col gap-1 p-2 md:px-3 overflow-x-auto flex-1">
          {items.map(([to, label, Icon, end]) => (
            <NavLink key={to} to={to} end={end} className={link}>
              <Icon size={18} /> <span className="whitespace-nowrap">{label}</span>
              {to === '/notifications' && unread > 0 && <span className="ml-auto rounded-full bg-signal-amber px-1.5 text-xs font-bold">{unread}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="hidden md:block border-t border-white/10 p-4">
          <div className="text-sm font-medium">{user.full_name || user.username}</div>
          <button className="mt-2 flex items-center gap-2 text-sm text-white/70 hover:text-white"
            onClick={() => { logout(); navigate('/login') }}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-5 md:p-8 max-w-[1200px] w-full"><Outlet /></main>
    </div>
  )
}
