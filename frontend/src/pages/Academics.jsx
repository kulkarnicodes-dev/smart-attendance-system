import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { api } from '../api'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader } from '../components/ui.jsx'

const TABS = ['Courses & subjects', 'Teacher assignments', 'Enrollment', 'Import students']

export default function Academics() {
  const [tab, setTab] = useState(0)
  const [msg, setMsg] = useState({ kind: 'ok', text: '' })
  const courses = useAsync(() => api('/api/academics/courses'))
  const subjects = useAsync(() => api('/api/academics/subjects'))
  const teachers = useAsync(() => api('/api/admin/users?role=teacher'))
  const assigns = useAsync(() => api('/api/academics/assignments'))
  const report = (e) => setMsg({ kind: 'error', text: e.message })
  const ok = (text) => setMsg({ kind: 'ok', text })
  const run = async (fn, after) => { try { await fn(); after?.() } catch (e) { report(e) } }

  // forms state
  const [c, setC] = useState({ code: '', name: '' })
  const [s, setS] = useState({ code: '', name: '', course_id: '', semester: 1 })
  const [a, setA] = useState({ teacher_id: '', subject_id: '', division: '' })
  const [en, setEn] = useState({ subject_id: '', division: '' })
  const roster = useAsync(() => (en.subject_id ? api(`/api/academics/enrollments?subject_id=${en.subject_id}`) : Promise.resolve([])), [en.subject_id])
  const [csv, setCsv] = useState('student_id,name,roll_no,course,semester,division,email\n')

  return (
    <>
      <PageHeader title="Academic structure" subtitle="Courses, subjects, teachers, enrollments" />
      <div className="flex gap-1 mb-4 overflow-x-auto">
        {TABS.map((t, i) => <button key={t} onClick={() => { setTab(i); setMsg({ kind: 'ok', text: '' }) }}
          className={`btn whitespace-nowrap ${tab === i ? 'bg-ink text-white' : 'bg-white border border-paper-line'}`}>{t}</button>)}
      </div>
      <Alert kind={msg.kind}>{msg.text}</Alert>

      {tab === 0 && (
        <div className="grid lg:grid-cols-2 gap-5">
          <section className="card p-5 space-y-3"><h2 className="font-semibold">Courses</h2>
            <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); run(() => api('/api/academics/courses', { method: 'POST', body: c }), () => { setC({ code: '', name: '' }); courses.reload(); ok('Course added') }) }}>
              <input className="input !w-24" placeholder="MCA" value={c.code} onChange={(e) => setC({ ...c, code: e.target.value })} required />
              <input className="input" placeholder="Course name" value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} required />
              <button className="btn-primary">Add</button></form>
            {(courses.data || []).map((x) => <div key={x.id} className="flex justify-between text-sm border-t border-paper-line pt-2"><span><b>{x.code}</b> · {x.name}</span>
              <button aria-label="Delete course" className="text-ink-mute hover:text-signal-red" onClick={() => confirm('Delete course?') && run(() => api(`/api/academics/courses/${x.id}`, { method: 'DELETE' }), courses.reload)}><Trash2 size={15} /></button></div>)}
          </section>
          <section className="card p-5 space-y-3"><h2 className="font-semibold">Subjects</h2>
            <form className="grid grid-cols-2 gap-2" onSubmit={(e) => { e.preventDefault(); run(() => api('/api/academics/subjects', { method: 'POST', body: { ...s, course_id: +s.course_id, semester: +s.semester } }), () => { setS({ ...s, code: '', name: '' }); subjects.reload(); ok('Subject added') }) }}>
              <input className="input" placeholder="Code e.g. MCA101" value={s.code} onChange={(e) => setS({ ...s, code: e.target.value })} required />
              <input className="input" placeholder="Subject name" value={s.name} onChange={(e) => setS({ ...s, name: e.target.value })} required />
              <select className="input" value={s.course_id} onChange={(e) => setS({ ...s, course_id: e.target.value })} required><option value="">Course…</option>{(courses.data || []).map((x) => <option key={x.id} value={x.id}>{x.code}</option>)}</select>
              <input className="input" type="number" min={1} max={8} value={s.semester} onChange={(e) => setS({ ...s, semester: e.target.value })} aria-label="Semester" />
              <button className="btn-primary col-span-2">Add subject</button></form>
            <div className="max-h-72 overflow-y-auto">{(subjects.data || []).map((x) => <div key={x.id} className="flex justify-between text-sm border-t border-paper-line py-2"><span><b>{x.code}</b> · {x.name} <span className="text-ink-mute">(Sem {x.semester})</span></span>
              <button aria-label="Delete subject" className="text-ink-mute hover:text-signal-red" onClick={() => confirm('Delete subject?') && run(() => api(`/api/academics/subjects/${x.id}`, { method: 'DELETE' }), subjects.reload)}><Trash2 size={15} /></button></div>)}</div>
          </section>
        </div>)}

      {tab === 1 && (
        <section className="card p-5 space-y-4 max-w-3xl">
          <form className="grid sm:grid-cols-4 gap-2" onSubmit={(e) => { e.preventDefault(); run(() => api('/api/academics/assignments', { method: 'POST', body: { ...a, teacher_id: +a.teacher_id, subject_id: +a.subject_id } }), () => { assigns.reload(); ok('Assigned') }) }}>
            <select className="input" value={a.teacher_id} onChange={(e) => setA({ ...a, teacher_id: e.target.value })} required><option value="">Teacher…</option>{(teachers.data || []).map((t) => <option key={t.id} value={t.id}>{t.full_name || t.username}</option>)}</select>
            <select className="input" value={a.subject_id} onChange={(e) => setA({ ...a, subject_id: e.target.value })} required><option value="">Subject…</option>{(subjects.data || []).map((x) => <option key={x.id} value={x.id}>{x.code}</option>)}</select>
            <input className="input" placeholder="Division (blank = all)" value={a.division} onChange={(e) => setA({ ...a, division: e.target.value })} />
            <button className="btn-primary">Assign</button></form>
          {(assigns.data || []).length === 0 ? <Empty>No assignments yet.</Empty> : (assigns.data || []).map((x) => (
            <div key={x.id} className="flex justify-between text-sm border-t border-paper-line pt-2"><span><b>{x.teacher}</b> teaches {x.code} · {x.subject} <span className="text-ink-mute">(Div {x.division || 'all'})</span></span>
              <button aria-label="Remove assignment" className="text-ink-mute hover:text-signal-red" onClick={() => run(() => api(`/api/academics/assignments/${x.id}`, { method: 'DELETE' }), assigns.reload)}><Trash2 size={15} /></button></div>))}
        </section>)}

      {tab === 2 && (
        <section className="card p-5 space-y-4 max-w-3xl">
          <p className="text-sm text-ink-soft">A student can only appear in a lecture roster if they are enrolled in that subject. "Enroll class" adds every student whose course and semester match the subject.</p>
          <div className="grid sm:grid-cols-3 gap-2">
            <select className="input" value={en.subject_id} onChange={(e) => setEn({ ...en, subject_id: e.target.value })}><option value="">Subject…</option>{(subjects.data || []).map((x) => <option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}</select>
            <input className="input" placeholder="Division (optional)" value={en.division} onChange={(e) => setEn({ ...en, division: e.target.value })} />
            <button className="btn-primary" disabled={!en.subject_id} onClick={() => run(async () => { const r = await api('/api/academics/enrollments/bulk', { method: 'POST', body: { subject_id: +en.subject_id, division: en.division } }); ok(`${r.added} student(s) enrolled`) }, roster.reload)}>Enroll class</button>
          </div>
          {en.subject_id && <div><h3 className="font-semibold text-sm mb-2">Enrolled ({(roster.data || []).length})</h3>
            <div className="max-h-72 overflow-y-auto">{(roster.data || []).map((x) => <div key={x.id} className="flex justify-between text-sm border-t border-paper-line py-1.5"><span>{x.roll_no} · {x.name} <span className="text-ink-mute">Div {x.division}</span></span>
              <button aria-label="Unenroll" className="text-ink-mute hover:text-signal-red" onClick={() => run(() => api(`/api/academics/enrollments?subject_id=${en.subject_id}&student_pk=${x.id}`, { method: 'DELETE' }), roster.reload)}><Trash2 size={14} /></button></div>)}</div></div>}
        </section>)}

      {tab === 3 && (
        <section className="card p-5 space-y-3 max-w-3xl">
          <p className="text-sm text-ink-soft">Paste a college list (CSV with header). Imported students can then register with the same Student ID and roll number; if the email matches, the account is approved automatically.</p>
          <textarea className="input font-mono text-xs" rows={9} value={csv} onChange={(e) => setCsv(e.target.value)} />
          <button className="btn-primary" onClick={() => run(async () => { const r = await api('/api/academics/import-students', { method: 'POST', body: { csv } }); setMsg({ kind: r.errors.length ? 'warn' : 'ok', text: `Added ${r.added}, skipped ${r.skipped_existing} existing.${r.errors.length ? ' Problems: ' + r.errors.join('; ') : ''}` }) })}>Import</button>
        </section>)}
    </>
  )
}
