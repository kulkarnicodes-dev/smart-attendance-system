import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { api, today } from '../api'
import { useAuth } from '../auth.jsx'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader, StatusPill } from '../components/ui.jsx'

export default function Sessions() {
  const { user } = useAuth()
  const nav = useNavigate()
  const list = useAsync(() => api('/api/sessions'))
  const subjects = useAsync(() => api('/api/academics/subjects'))
  const assigned = useAsync(() => api('/api/academics/assignments'))
  const teachers = useAsync(() => (user.role === 'admin' ? api('/api/admin/users?role=teacher') : Promise.resolve([])))
  const [show, setShow] = useState(false)
  const [f, setF] = useState({ subject_id: '', division: '', date: today(), start_time: '09:00', duration_min: 60, topic: '', teacher_id: '' })
  const [err, setErr] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  // teachers can only pick their assigned subjects
  const choices = user.role === 'admin' ? subjects.data : (subjects.data || []).filter((s) => (assigned.data || []).some((a) => a.subject_id === s.id))

  const create = async (e) => {
    e.preventDefault(); setErr('')
    try {
      const s = await api('/api/sessions', { method: 'POST', body: { ...f, subject_id: +f.subject_id, duration_min: +f.duration_min, teacher_id: f.teacher_id ? +f.teacher_id : null } })
      nav(`/sessions/${s.id}`)
    } catch (ex) { setErr(ex.message) }
  }

  return (
    <>
      <PageHeader title="Lecture sessions" subtitle="Every lecture has its own roster and attendance">
        <button className="btn-primary" onClick={() => setShow(!show)}><Plus size={16} /> New session</button>
      </PageHeader>
      <Alert>{list.err}</Alert>
      {show && (
        <form onSubmit={create} className="card p-5 mb-5 grid sm:grid-cols-3 gap-3">
          <div className="sm:col-span-3"><Alert>{err}</Alert></div>
          <div><label className="label">Subject</label>
            <select className="input" value={f.subject_id} onChange={set('subject_id')} required>
              <option value="">Select…</option>{(choices || []).map((s) => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></div>
          <div><label className="label">Division (blank = all)</label><input className="input" value={f.division} onChange={set('division')} placeholder="A" /></div>
          <div><label className="label">Date</label><input type="date" className="input" value={f.date} onChange={set('date')} required /></div>
          <div><label className="label">Start time</label><input type="time" className="input" value={f.start_time} onChange={set('start_time')} required /></div>
          <div><label className="label">Duration (min)</label><input type="number" className="input" value={f.duration_min} onChange={set('duration_min')} min={10} max={300} /></div>
          <div><label className="label">Topic (optional)</label><input className="input" value={f.topic} onChange={set('topic')} /></div>
          {user.role === 'admin' && <div><label className="label">Teacher</label>
            <select className="input" value={f.teacher_id} onChange={set('teacher_id')}><option value="">Me</option>
              {(teachers.data || []).map((t) => <option key={t.id} value={t.id}>{t.full_name || t.username}</option>)}</select></div>}
          <div className="sm:col-span-3"><button className="btn-primary">Create & open</button></div>
        </form>)}

      <div className="card overflow-x-auto">
        {!list.data ? <Empty>Loading…</Empty> : list.data.length === 0 ? <Empty>No sessions yet. Create one for your next lecture.</Empty> : (
          <table className="w-full">
            <thead><tr>{['Date', 'Time', 'Subject', 'Div', 'Present / Roster', 'Status', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{list.data.map((s) => (
              <tr key={s.id}>
                <td className="td">{s.date}</td><td className="td">{s.start}</td>
                <td className="td font-medium">{s.subject}{user.role === 'admin' && <div className="text-xs text-ink-mute">{s.teacher}</div>}</td>
                <td className="td">{s.division || 'all'}</td>
                <td className="td">{(s.counts.Present || 0) + (s.counts.Late || 0)} / {s.roster}</td>
                <td className="td"><StatusPill status={s.status} /></td>
                <td className="td text-right"><Link to={`/sessions/${s.id}`} className="btn-ghost !py-1.5">{s.status === 'open' ? 'Open' : 'View'}</Link></td>
              </tr>))}</tbody>
          </table>)}
      </div>
    </>
  )
}
