import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { useAuth } from '../auth.jsx'
import { useAsync } from '../components/hooks.js'
import { Alert, DAYS, Empty, PageHeader, PercentBar, Stat, StatusPill } from '../components/ui.jsx'

export default function Dashboard() {
  const { user } = useAuth()
  if (user.role === 'admin') return <AdminHome />
  if (user.role === 'teacher') return <TeacherHome />
  return <StudentHome />
}

const dateLabel = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

function AdminHome() {
  const stats = useAsync(() => api('/api/admin/stats'))
  const ov = useAsync(() => api('/api/analytics/overview'))
  const d = stats.data
  return (
    <>
      <PageHeader title="Admin dashboard" subtitle={dateLabel} />
      <Alert>{stats.err || ov.err}</Alert>
      {d && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="Students" value={d.students} />
          <Stat label="Active teachers" value={d.teachers} />
          <Stat label="Pending approvals" value={d.pending_users} tone={d.pending_users ? 'text-signal-amber' : ''} />
          <Stat label="Open sessions" value={d.open_sessions} tone="text-brand" />
        </div>
      )}
      {d?.pending_users > 0 && <div className="mt-4 card p-4 flex items-center justify-between text-sm">
        <span>{d.pending_users} student account(s) waiting for approval.</span><Link to="/users" className="btn-primary">Review</Link></div>}
      {d?.students_without_face > 0 && <p className="mt-3 text-sm text-ink-mute">{d.students_without_face} student(s) have no face data yet.</p>}
      {ov.data && (
        <div className="mt-6 grid lg:grid-cols-2 gap-4">
          <section className="card p-5">
            <h2 className="font-semibold mb-3">Attendance % by subject</h2>
            {ov.data.by_subject.length === 0 ? <Empty>No finalized sessions yet.</Empty> : (
              <div className="h-64"><ResponsiveContainer><BarChart data={ov.data.by_subject}>
                <CartesianGrid vertical={false} stroke="#DCE4E9" strokeDasharray="3 3" />
                <XAxis dataKey="code" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} width={32} />
                <Tooltip formatter={(v) => `${v}%`} /><Bar dataKey="percent" fill="#0E7C7B" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>)}
          </section>
          <section className="card p-5">
            <h2 className="font-semibold mb-3">Below {ov.data.threshold}% ({ov.data.below.length})</h2>
            {ov.data.below.length === 0 ? <p className="text-sm text-ink-mute">Nobody is below the threshold.</p> : (
              <ul className="max-h-64 overflow-y-auto">{ov.data.below.slice(0, 12).map((b, i) => (
                <li key={i} className="flex justify-between border-t border-paper-line py-2 text-sm">
                  <span>{b.name} <span className="text-ink-mute">· {b.subject}</span></span><b className="text-signal-red">{b.percent}%</b></li>))}</ul>)}
          </section>
        </div>
      )}
    </>
  )
}

function TeacherHome() {
  const nav = useNavigate()
  const today = useAsync(() => api('/api/timetable/today'))
  const open = useAsync(() => api('/api/sessions?status=open'))
  const corr = useAsync(() => api('/api/corrections?status=pending'))
  const [err, setErr] = useState('')
  const start = async (e) => {
    try { const s = await api(`/api/sessions/from-timetable/${e.id}`, { method: 'POST' }); nav(`/sessions/${s.id}`) } catch (x) { setErr(x.message) }
  }
  return (
    <>
      <PageHeader title="Teacher dashboard" subtitle={dateLabel}><Link to="/sessions" className="btn-primary">All sessions</Link></PageHeader>
      <Alert>{err || today.err}</Alert>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Stat label="Lectures today" value={today.data?.length ?? '–'} />
        <Stat label="Open sessions" value={open.data?.length ?? '–'} tone="text-brand" />
        <Stat label="Pending corrections" value={corr.data?.length ?? '–'} tone={corr.data?.length ? 'text-signal-amber' : ''} />
      </div>
      <section className="card">
        <h2 className="font-semibold p-5 pb-3">Today's timetable</h2>
        {!today.data ? <Empty>Loading…</Empty> : today.data.length === 0 ? <Empty>No lectures scheduled today. You can still create a session manually.</Empty> : today.data.map((e) => (
          <div key={e.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 border-t border-paper-line text-sm">
            <div><div className="font-medium">{e.subject} <span className="text-ink-mute">· Div {e.division || 'all'}</span></div>
              <div className="text-xs text-ink-mute">{e.start}–{e.end} {e.room && `· Room ${e.room}`}</div></div>
            {e.session_id
              ? <Link to={`/sessions/${e.session_id}`} className="btn-ghost">{e.session_status === 'open' ? 'Continue' : 'View'} <StatusPill status={e.session_status} /></Link>
              : <button className="btn-primary" onClick={() => start(e)}>Start session</button>}
          </div>))}
      </section>
    </>
  )
}

function StudentHome() {
  const sum = useAsync(() => api('/api/analytics/me'))
  const tt = useAsync(() => api('/api/timetable'))
  const d = sum.data
  const todayIdx = (new Date().getDay() + 6) % 7
  const low = d?.subjects.filter((s) => s.below) || []
  return (
    <>
      <PageHeader title={d ? `Hello, ${d.student.name.split(' ')[0]}` : 'Dashboard'} subtitle={dateLabel} />
      <Alert>{sum.err}</Alert>
      {d && d.student.face_count === 0 && <div className="card p-4 mb-4 flex items-center justify-between text-sm">
        <span>Your face data is not registered yet, so face attendance cannot recognise you.</span><Link to="/my-face" className="btn-primary">Register face</Link></div>}
      {low.map((s) => <Alert key={s.subject_id} kind="warn">Low attendance in <b>{s.subject}</b>: {s.percent}% (minimum {d.threshold}%).
        Attend the next {s.needed} lecture(s) in a row to get back above the limit.</Alert>)}
      {d && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="Overall attendance" value={d.overall.percent == null ? '–' : `${d.overall.percent}%`} tone={d.overall.percent != null && d.overall.percent < d.threshold ? 'text-signal-red' : 'text-brand'} />
          <Stat label="Lectures attended" value={`${d.overall.attended}/${d.overall.total}`} />
          <Stat label="Subjects below limit" value={low.length} tone={low.length ? 'text-signal-red' : ''} />
          <Stat label="Required minimum" value={`${d.threshold}%`} />
        </div>
      )}
      <div className="mt-6 grid lg:grid-cols-5 gap-4">
        <section className="card p-5 lg:col-span-3">
          <h2 className="font-semibold mb-3">Subject-wise attendance</h2>
          {!d || d.subjects.length === 0 ? <p className="text-sm text-ink-mute">No finalized lectures yet.</p> : d.subjects.map((s) => (
            <div key={s.subject_id} className="mb-4">
              <div className="flex justify-between text-sm mb-1"><span className="font-medium">{s.subject}</span>
                <span className={s.below ? 'text-signal-red font-semibold' : ''}>{s.percent}% <span className="text-ink-mute">({s.attended}/{s.total})</span></span></div>
              <PercentBar value={s.percent} below={s.below} />
            </div>))}
        </section>
        <section className="card lg:col-span-2">
          <h2 className="font-semibold p-5 pb-3">Today's lectures</h2>
          {(tt.data || []).filter((e) => e.weekday === todayIdx).length === 0 ? <p className="px-5 pb-5 text-sm text-ink-mute">No lectures today.</p>
            : tt.data.filter((e) => e.weekday === todayIdx).map((e) => (
              <div key={e.id} className="px-5 py-2.5 border-t border-paper-line text-sm"><div className="font-medium">{e.subject}</div>
                <div className="text-xs text-ink-mute">{e.start}–{e.end} · {e.teacher} {e.room && `· Room ${e.room}`}</div></div>))}
          <div className="px-5 py-3 border-t border-paper-line"><Link to="/timetable" className="text-sm text-brand font-semibold">Full timetable →</Link></div>
        </section>
      </div>
    </>
  )
}
