import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth.jsx'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader, StatusPill } from '../components/ui.jsx'

export default function Corrections() {
  const { user } = useAuth()
  const [filter, setFilter] = useState(user.role === 'student' ? '' : 'pending')
  const list = useAsync(() => api(`/api/corrections${filter ? `?status=${filter}` : ''}`), [filter])
  const [err, setErr] = useState('')
  const staff = user.role !== 'student'

  const decide = async (c, approve) => {
    let note = ''
    if (!approve) { note = prompt('Reason for rejecting (shown to the student):') || ''; if (note.trim().length < 3) return }
    try { await api(`/api/corrections/${c.id}/decide`, { method: 'POST', body: { approve, note } }); list.reload() } catch (e) { setErr(e.message) }
  }

  return (
    <>
      <PageHeader title="Correction requests" subtitle={staff ? 'Approve or reject attendance corrections from students' : 'Requests you have submitted. Start a new one from My attendance.'}>
        <select className="input !w-40" value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by status">
          <option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select>
      </PageHeader>
      <Alert>{err || list.err}</Alert>
      <div className="card overflow-x-auto">
        {!list.data ? <Empty>Loading…</Empty> : list.data.length === 0 ? <Empty>No requests.</Empty> : (
          <table className="w-full"><thead><tr>{[staff ? 'Student' : 'Subject', 'Lecture', 'Wants', 'Reason', 'Status', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{list.data.map((c) => (
              <tr key={c.id}>
                <td className="td">{staff ? <>{c.student}<div className="text-xs text-ink-mute">{c.roll_no}</div></> : c.subject}</td>
                <td className="td">{staff && <div>{c.subject}</div>}<div className="text-xs text-ink-mute">{c.date} {c.start}</div></td>
                <td className="td">{c.requested_status}</td><td className="td max-w-xs">{c.reason}{c.decision_note && <div className="text-xs text-ink-mute mt-1">Reply: {c.decision_note}</div>}</td>
                <td className="td"><StatusPill status={c.status} /></td>
                <td className="td">{staff && c.status === 'pending' && <div className="flex gap-2 justify-end">
                  <button className="btn-primary !py-1" onClick={() => decide(c, true)}>Approve</button>
                  <button className="btn-danger !py-1" onClick={() => decide(c, false)}>Reject</button></div>}</td>
              </tr>))}</tbody></table>)}
      </div>
    </>
  )
}
