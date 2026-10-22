import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../auth.jsx'
import { useAsync } from '../components/hooks.js'
import { Alert, DAYS, Empty, PageHeader } from '../components/ui.jsx'

export default function Timetable() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const tt = useAsync(() => api('/api/timetable'))
  const subjects = useAsync(() => (isAdmin ? api('/api/academics/subjects') : Promise.resolve([])))
  const teachers = useAsync(() => (isAdmin ? api('/api/admin/users?role=teacher') : Promise.resolve([])))
  const [f, setF] = useState({ subject_id: '', teacher_id: '', division: 'A', weekday: 0, start_time: '09:00', duration_min: 60, room: '' })
  const [err, setErr] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const add = async (e) => {
    e.preventDefault(); setErr('')
    try { await api('/api/timetable', { method: 'POST', body: { ...f, subject_id: +f.subject_id, teacher_id: +f.teacher_id, weekday: +f.weekday, duration_min: +f.duration_min } }); tt.reload() }
    catch (ex) { setErr(ex.message) }
  }
  const del = async (id) => { if (confirm('Remove this slot?')) { await api(`/api/timetable/${id}`, { method: 'DELETE' }); tt.reload() } }

  const byDay = DAYS.map((d, i) => ({ d, items: (tt.data || []).filter((e) => e.weekday === i) })).filter((x) => x.items.length)

  return (
    <>
      <PageHeader title="Timetable" subtitle={isAdmin ? 'Conflicts (teacher, room, division) are blocked automatically' : 'Your weekly schedule'} />
      <Alert>{tt.err}</Alert>
      {isAdmin && (
        <form onSubmit={add} className="card p-5 mb-5 grid sm:grid-cols-4 gap-3">
          <div className="sm:col-span-4"><Alert>{err}</Alert></div>
          <div><label className="label">Subject</label><select className="input" value={f.subject_id} onChange={set('subject_id')} required>
            <option value="">Select…</option>{(subjects.data || []).map((s) => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></div>
          <div><label className="label">Teacher</label><select className="input" value={f.teacher_id} onChange={set('teacher_id')} required>
            <option value="">Select…</option>{(teachers.data || []).map((t) => <option key={t.id} value={t.id}>{t.full_name || t.username}</option>)}</select></div>
          <div><label className="label">Division</label><input className="input" value={f.division} onChange={set('division')} /></div>
          <div><label className="label">Day</label><select className="input" value={f.weekday} onChange={set('weekday')}>{DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}</select></div>
          <div><label className="label">Start</label><input type="time" className="input" value={f.start_time} onChange={set('start_time')} required /></div>
          <div><label className="label">Duration (min)</label><input type="number" className="input" value={f.duration_min} onChange={set('duration_min')} /></div>
          <div><label className="label">Room</label><input className="input" value={f.room} onChange={set('room')} /></div>
          <div className="flex items-end"><button className="btn-primary w-full">Add slot</button></div>
        </form>)}
      {!tt.data ? <Empty>Loading…</Empty> : byDay.length === 0 ? <div className="card"><Empty>No timetable entries yet.</Empty></div> : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {byDay.map(({ d, items }) => (
            <section key={d} className="card"><h2 className="font-semibold px-4 py-3 bg-paper/60 rounded-t-lg">{d}</h2>
              {items.map((e) => (
                <div key={e.id} className="flex justify-between gap-2 px-4 py-2.5 border-t border-paper-line text-sm">
                  <div><div className="font-medium">{e.subject}</div><div className="text-xs text-ink-mute">{e.start}–{e.end} · {e.teacher} · Div {e.division || 'all'}{e.room && ` · ${e.room}`}</div></div>
                  {isAdmin && <button className="text-ink-mute hover:text-signal-red" onClick={() => del(e.id)} aria-label="Remove slot"><Trash2 size={15} /></button>}
                </div>))}
            </section>))}
        </div>)}
    </>
  )
}
