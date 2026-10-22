import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ScanFace } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { Alert } from '../components/ui.jsx'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setU] = useState('')
  const [password, setP] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try { await login(username, password); navigate('/') }
    catch (ex) { setErr(ex.message) }
    finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen grid md:grid-cols-2">
      <div className="hidden md:flex bg-ink text-white p-12 flex-col justify-between">
        <ScanFace size={40} className="text-brand" />
        <div>
          <h1 className="text-4xl font-bold leading-tight">One system for admins,<br />teachers and students.</h1>
          <p className="mt-4 text-white/70 max-w-md">
            Lecture-wise face-recognition attendance, timetables, analytics and correction requests,
            each role with its own portal.
          </p>
        </div>
        <p className="text-sm text-white/50">Smart Attendance Management System · MCA Mini Project</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-sm space-y-4">
          <h2 className="text-2xl font-bold">Sign in</h2>
          <Alert>{err}</Alert>
          <div><label className="label" htmlFor="u">Username</label>
            <input id="u" className="input" value={username} onChange={(e) => setU(e.target.value)} autoFocus required /></div>
          <div><label className="label" htmlFor="p">Password</label>
            <input id="p" type="password" className="input" value={password} onChange={(e) => setP(e.target.value)} required /></div>
          <button className="btn-primary w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
          <p className="text-sm text-ink-mute text-center">New student? <Link to="/register" className="text-brand font-semibold">Create an account</Link></p>
        </form>
      </div>
    </div>
  )
}
