import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Camera, Plus, Trash2 } from 'lucide-react'
import { api, qs } from '../api'
import { useAuth } from '../auth.jsx'
import { Alert, Empty, PageHeader } from '../components/ui.jsx'

export default function Students() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const [rows, setRows] = useState(null)
  const [q, setQ] = useState('')
  const [err, setErr] = useState('')

  const load = () => api('/api/students' + qs({ q })).then(setRows).catch((e) => setErr(e.message))
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [q])

  const remove = async (s) => {
    if (!confirm(`Delete ${s.name}? This permanently removes their face data, enrollments and attendance records.`)) return
    try { await api(`/api/students/${s.id}`, { method: 'DELETE' }); load() } catch (e) { setErr(e.message) }
  }

  return (
    <>
      <PageHeader title="Students" subtitle="Registered students and their face data">
        {isAdmin && <Link to="/students/new" className="btn-primary"><Plus size={16} /> Add student</Link>}
      </PageHeader>
      <Alert>{err}</Alert>
      <input className="input max-w-sm mb-4" placeholder="Search name, roll no or PRN" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="card overflow-x-auto">
        {!rows ? <Empty>Loading…</Empty> : rows.length === 0 ? <Empty>No students found.</Empty> : (
          <table className="w-full">
            <thead><tr>{['Roll no', 'Name', 'Sem / Div', 'Account', 'Face samples', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td className="td font-medium">{s.roll_no}</td>
                  <td className="td">{s.name}<div className="text-xs text-ink-mute">{s.student_id}</div></td>
                  <td className="td">{s.semester} / {s.division}</td>
                  <td className="td">{s.user_id ? <span className="pill bg-emerald-50 text-signal-green">Linked</span> : <span className="pill bg-paper text-ink-mute">No login</span>}</td>
                  <td className="td"><span className={`pill ${s.face_count >= 10 ? 'bg-emerald-50 text-signal-green' : 'bg-amber-50 text-signal-amber'}`}>
                    {s.face_count === 0 ? 'Not captured' : `${s.face_count} captured`}</span></td>
                  <td className="td"><div className="flex gap-2 justify-end">
                    <Link to={`/students/${s.id}/face`} className="btn-ghost !py-1.5"><Camera size={15} /> Face</Link>
                    {isAdmin && <button className="btn-danger !py-1.5" onClick={() => remove(s)} aria-label={`Delete ${s.name}`}><Trash2 size={15} /></button>}
                  </div></td>
                </tr>))}
            </tbody>
          </table>)}
      </div>
    </>
  )
}
