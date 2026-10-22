import { useState } from 'react'
import { api } from '../api'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader } from '../components/ui.jsx'

export default function Audit() {
  const [action, setAction] = useState('')
  const logs = useAsync(() => api(`/api/admin/audit${action ? `?action=${action}` : ''}`), [action])
  return (
    <>
      <PageHeader title="Audit log" subtitle="Who changed what, and when (newest first)">
        <select className="input !w-44" value={action} onChange={(e) => setAction(e.target.value)} aria-label="Filter">
          <option value="">All actions</option>{['attendance', 'session', 'user', 'correction', 'student', 'biometric', 'auth', 'settings', 'timetable'].map((a) => <option key={a}>{a}</option>)}</select>
      </PageHeader>
      <Alert>{logs.err}</Alert>
      <div className="card overflow-x-auto">
        {!logs.data ? <Empty>Loading…</Empty> : logs.data.length === 0 ? <Empty>No entries.</Empty> : (
          <table className="w-full"><thead><tr>{['When', 'Actor', 'Action', 'Entity', 'Detail'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{logs.data.map((l) => <tr key={l.id}><td className="td whitespace-nowrap text-ink-mute">{l.at.replace('T', ' ')}</td><td className="td">{l.actor}</td>
              <td className="td font-medium">{l.action}</td><td className="td">{l.entity} {l.entity_id}</td><td className="td max-w-md">{l.detail}</td></tr>)}</tbody></table>)}
      </div>
    </>
  )
}
