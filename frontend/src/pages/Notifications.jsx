import { api } from '../api'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader } from '../components/ui.jsx'

export default function Notifications() {
  const n = useAsync(() => api('/api/notifications'))
  const readAll = async () => { await api('/api/notifications/read-all', { method: 'POST' }); n.reload() }
  return (
    <>
      <PageHeader title="Notifications" subtitle="Absences, low-attendance alerts, approvals and corrections">
        {n.data?.unread > 0 && <button className="btn-ghost" onClick={readAll}>Mark all read</button>}
      </PageHeader>
      <Alert>{n.err}</Alert>
      <div className="card">
        {!n.data ? <Empty>Loading…</Empty> : n.data.items.length === 0 ? <Empty>Nothing yet.</Empty> : n.data.items.map((x) => (
          <div key={x.id} className={`px-5 py-3 border-b border-paper-line last:border-0 ${x.read ? '' : 'bg-brand-tint/40'}`}>
            <div className="flex justify-between gap-3"><div className="font-medium text-sm">{x.title}</div><div className="text-xs text-ink-mute whitespace-nowrap">{x.at.replace('T', ' ')}</div></div>
            <div className="text-sm text-ink-soft">{x.body}</div>
          </div>))}
      </div>
    </>
  )
}
