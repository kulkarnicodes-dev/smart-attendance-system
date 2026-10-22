import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Alert } from '../components/ui.jsx'

const empty = { full_name: '', username: '', password: '', email: '', student_id: '', roll_no: '', course: 'MCA', semester: 1, division: 'A', consent: false }

export default function Register() {
  const [f, setF] = useState(empty)
  const [err, setErr] = useState('')
  const [done, setDone] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const field = (k, label, p = {}) => (
    <div key={k}><label className="label" htmlFor={k}>{label}</label>
      <input id={k} className="input" value={f[k]} onChange={set(k)} required {...p} /></div>
  )

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr('')
    try { setDone(await api('/api/auth/register', { method: 'POST', body: { ...f, semester: Number(f.semester) || 1 } })) }
    catch (ex) { setErr(ex.message) } finally { setBusy(false) }
  }

  if (done) return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="card p-8 max-w-md text-center space-y-4">
        <h1 className="text-2xl font-bold">{done.approved ? 'You are all set' : 'Registration received'}</h1>
        <p className="text-ink-soft">{done.message}</p>
        <Link to="/login" className="btn-primary">Go to sign in</Link>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={submit} className="card p-6 w-full max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Student registration</h1>
        <p className="text-sm text-ink-mute">An administrator approves new accounts before you can sign in.</p>
        <Alert>{err}</Alert>
        <div className="grid sm:grid-cols-2 gap-4">
          {field('full_name', 'Full name')}
          {field('email', 'Email', { type: 'email' })}
          {field('student_id', 'PRN / Student ID')}
          {field('roll_no', 'Roll number', { placeholder: 'MCA001' })}
          {field('course', 'Course')}
          {field('semester', 'Semester', { type: 'number', min: 1, max: 8 })}
          {field('division', 'Division')}
          {field('username', 'Choose a username', { minLength: 3, autoComplete: 'username' })}
          {field('password', 'Password (min 6)', { type: 'password', minLength: 6, autoComplete: 'new-password' })}
        </div>
        <label className="flex gap-3 items-start rounded-md bg-brand-tint p-3 text-sm">
          <input type="checkbox" className="mt-1" checked={f.consent} onChange={set('consent')} />
          <span>I consent to my face data (numeric embeddings, not photos) being stored and used only for attendance.
            I can ask for it to be deleted at any time.</span>
        </label>
        <div className="flex items-center gap-3">
          <button className="btn-primary" disabled={busy || !f.consent}>{busy ? 'Submitting…' : 'Register'}</button>
          <Link to="/login" className="text-sm text-brand font-semibold">Back to sign in</Link>
        </div>
      </form>
    </div>
  )
}
