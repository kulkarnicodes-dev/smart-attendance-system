import { useState } from 'react'
import { Download } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, download } from '../api'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader } from '../components/ui.jsx'

function Chart({ data, x, title }) {
  return (
    <section className="card p-5">
      <h2 className="font-semibold mb-3">{title}</h2>
      {data.length === 0 ? <Empty>No finalized sessions yet.</Empty> : (
        <div className="h-56"><ResponsiveContainer><BarChart data={data}><CartesianGrid vertical={false} stroke="#DCE4E9" strokeDasharray="3 3" />
          <XAxis dataKey={x} tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} width={32} tickLine={false} axisLine={false} />
          <Tooltip formatter={(v) => `${v}%`} /><Bar dataKey="percent" fill="#0E7C7B" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>)}
    </section>
  )
}

export default function Reports() {
  const ov = useAsync(() => api('/api/analytics/overview'))
  const subjects = useAsync(() => api('/api/academics/subjects'))
  const [sub, setSub] = useState('')
  const detail = useAsync(() => (sub ? api(`/api/analytics/subject/${sub}`) : Promise.resolve(null)), [sub])
  const [err, setErr] = useState('')
  const d = ov.data

  return (
    <>
      <PageHeader title="Reports & analytics" subtitle={d ? `Threshold ${d.threshold}% · finalized lectures only` : ''} />
      <Alert>{err || ov.err}</Alert>
      {d && (
        <>
          <div className="grid lg:grid-cols-3 gap-4">
            <Chart data={d.by_subject} x="code" title="By subject" />
            <Chart data={d.by_division} x="division" title="By division" />
            <Chart data={d.monthly} x="month" title="By month" />
          </div>
          <section className="card mt-5 overflow-x-auto">
            <h2 className="font-semibold p-5 pb-3">Below {d.threshold}%: needs attention ({d.below.length})</h2>
            {d.below.length === 0 ? <Empty>Nobody is below the threshold.</Empty> : (
              <table className="w-full"><thead><tr>{['Student', 'Subject', 'Attendance', 'Lectures to recover'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
                <tbody>{d.below.map((b, i) => <tr key={i}><td className="td">{b.name} <span className="text-ink-mute">{b.roll_no}</span></td><td className="td">{b.subject}</td>
                  <td className="td text-signal-red font-semibold">{b.percent}% <span className="font-normal text-ink-mute">({b.attended}/{b.total})</span></td><td className="td">{b.needed} in a row</td></tr>)}</tbody></table>)}
          </section>
        </>)}

      <section className="card mt-5 p-5">
        <h2 className="font-semibold mb-3">Subject register</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          <select className="input !w-72" value={sub} onChange={(e) => setSub(e.target.value)}><option value="">Select subject…</option>{(subjects.data || []).map((s) => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select>
          <button className="btn-ghost" disabled={!sub} onClick={() => download(`/api/analytics/export/subject/${sub}`, `subject_${sub}.csv`).catch((e) => setErr(e.message))}><Download size={16} /> Export full register (CSV)</button>
        </div>
        {detail.err && <Alert>{detail.err}</Alert>}
        {detail.data && (
          <table className="w-full"><thead><tr>{['Roll no', 'Name', 'Div', 'Attended', 'Percent'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{detail.data.students.map((s) => <tr key={s.student_pk}><td className="td font-medium">{s.roll_no}</td><td className="td">{s.name}</td><td className="td">{s.division}</td>
              <td className="td">{s.attended}/{s.total}</td><td className={`td ${s.below ? 'text-signal-red font-semibold' : ''}`}>{s.percent == null ? '–' : `${s.percent}%`}</td></tr>)}</tbody></table>)}
      </section>
    </>
  )
}
