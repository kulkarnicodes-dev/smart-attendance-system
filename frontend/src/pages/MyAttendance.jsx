import { useState } from 'react'
import { Download } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, download } from '../api'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader, PercentBar, StatusPill } from '../components/ui.jsx'

export default function MyAttendance() {
  const sum = useAsync(() => api('/api/analytics/me'))
  const [sub, setSub] = useState('')
  const pk = sum.data?.student.id
  const hist = useAsync(() => (pk ? api(`/api/analytics/student/${pk}/history${sub ? `?subject_id=${sub}` : ''}`) : Promise.resolve(null)), [pk, sub])
  const [req, setReq] = useState(null)
  const [form, setForm] = useState({ requested_status: 'Present', reason: '' })
  const [msg, setMsg] = useState({ kind: 'ok', text: '' })
  const d = sum.data

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api('/api/corrections', { method: 'POST', body: { session_id: req.session_id, ...form } })
      setMsg({ kind: 'ok', text: 'Request sent to your teacher.' }); setReq(null); setForm({ requested_status: 'Present', reason: '' }); hist.reload()
    } catch (ex) { setMsg({ kind: 'error', text: ex.message }) }
  }

  return (
    <>
      <PageHeader title="My attendance" subtitle="Finalized lectures only. Excused lectures are not counted.">
        {pk && <button className="btn-ghost" onClick={() => download(`/api/analytics/export/student/${pk}`, 'my_attendance.csv')}><Download size={16} /> Download CSV</button>}
      </PageHeader>
      <Alert>{sum.err || hist.err}</Alert>
      <Alert kind={msg.kind}>{msg.text}</Alert>
      {d && (
        <div className="grid lg:grid-cols-2 gap-5 mb-6">
          <section className="card p-5">
            <h2 className="font-semibold mb-3">By subject</h2>
            {d.subjects.length === 0 ? <p className="text-sm text-ink-mute">Nothing recorded yet.</p> : d.subjects.map((s) => (
              <button key={s.subject_id} onClick={() => setSub(String(sub === String(s.subject_id) ? '' : s.subject_id))} className="block w-full text-left mb-4">
                <div className="flex justify-between text-sm mb-1"><span className={`font-medium ${String(s.subject_id) === sub ? 'text-brand' : ''}`}>{s.subject}</span>
                  <span className={s.below ? 'text-signal-red font-semibold' : ''}>{s.percent}% · {s.attended}/{s.total}{s.late ? ` (${s.late} late)` : ''}{s.excused ? ` · ${s.excused} excused` : ''}</span></div>
                <PercentBar value={s.percent} below={s.below} />
                {s.below && <div className="text-xs text-signal-red mt-1">Attend the next {s.needed} lecture(s) to reach {d.threshold}%</div>}
              </button>))}
          </section>
          <section className="card p-5">
            <h2 className="font-semibold mb-3">Monthly trend</h2>
            {d.monthly.length === 0 ? <p className="text-sm text-ink-mute">No data yet.</p> : (
              <div className="h-56"><ResponsiveContainer><BarChart data={d.monthly}><CartesianGrid vertical={false} stroke="#DCE4E9" strokeDasharray="3 3" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} width={32} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => `${v}%`} /><Bar dataKey="percent" fill="#0E7C7B" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>)}
          </section>
        </div>)}

      {req && (
        <form onSubmit={submit} className="card p-5 mb-5 space-y-3 max-w-xl">
          <h2 className="font-semibold">Correction request: {req.subject}, {req.date} {req.start}</h2>
          <select className="input" value={form.requested_status} onChange={(e) => setForm({ ...form, requested_status: e.target.value })}>
            {['Present', 'Late', 'Excused'].map((x) => <option key={x}>{x}</option>)}</select>
          <textarea className="input" rows={3} required minLength={10} placeholder="Explain why this record is wrong (min 10 characters)" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
          <div className="flex gap-2"><button className="btn-primary">Send request</button><button type="button" className="btn-ghost" onClick={() => setReq(null)}>Cancel</button></div>
        </form>)}

      <div className="card overflow-x-auto">
        <h2 className="font-semibold p-5 pb-3">History {sub && <button className="ml-2 text-sm text-brand" onClick={() => setSub('')}>(show all subjects)</button>}</h2>
        {!hist.data ? <Empty>Loading…</Empty> : hist.data.length === 0 ? <Empty>No finalized lectures yet.</Empty> : (
          <table className="w-full"><thead><tr>{['Date', 'Time', 'Subject', 'Status', 'Source', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{hist.data.map((h) => (
              <tr key={h.session_id}><td className="td">{h.date}</td><td className="td">{h.start}</td><td className="td">{h.subject}</td>
                <td className="td"><StatusPill status={h.status} /></td><td className="td text-ink-mute capitalize">{h.method}</td>
                <td className="td text-right">{h.status === 'Absent' && (h.correction_pending ? <span className="pill bg-amber-50 text-signal-amber">Request pending</span>
                  : <button className="btn-ghost !py-1" onClick={() => { setReq(h); window.scrollTo(0, 0) }}>Request correction</button>)}</td></tr>))}</tbody></table>)}
      </div>
    </>
  )
}
