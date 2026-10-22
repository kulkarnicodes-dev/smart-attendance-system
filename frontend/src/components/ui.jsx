export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {subtitle && <p className="text-sm text-ink-mute mt-1">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}

export function Alert({ kind = 'error', children }) {
  if (!children) return null
  const c = kind === 'error' ? 'bg-red-50 border-red-200 text-signal-red'
    : kind === 'ok' ? 'bg-emerald-50 border-emerald-200 text-signal-green'
    : 'bg-amber-50 border-amber-200 text-signal-amber'
  return <div className={`rounded-md border px-3 py-2 text-sm ${c} mb-3`} role="alert">{children}</div>
}

const PILL = {
  Present: 'bg-emerald-50 text-signal-green', Late: 'bg-amber-50 text-signal-amber',
  Absent: 'bg-red-50 text-signal-red', Excused: 'bg-sky-50 text-sky-700',
  open: 'bg-emerald-50 text-signal-green', finalized: 'bg-paper text-ink-soft',
  pending: 'bg-amber-50 text-signal-amber', approved: 'bg-emerald-50 text-signal-green',
  rejected: 'bg-red-50 text-signal-red', active: 'bg-emerald-50 text-signal-green', disabled: 'bg-red-50 text-signal-red',
}
export function StatusPill({ status }) {
  if (!status) return <span className="pill bg-paper text-ink-mute">Not marked</span>
  return <span className={`pill ${PILL[status] || 'bg-paper text-ink-soft'}`}>{status}</span>
}

export function Empty({ children }) {
  return <div className="p-8 text-center text-sm text-ink-mute">{children}</div>
}

export function Stat({ label, value, tone }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-ink-mute">{label}</div>
      <div className={`mt-1 text-3xl font-bold ${tone || ''}`}>{value}</div>
    </div>
  )
}

export function PercentBar({ value, below }) {
  return (
    <div className="h-2 rounded bg-paper w-full">
      <div className={`h-2 rounded ${below ? 'bg-signal-red' : 'bg-brand'}`} style={{ width: `${Math.min(100, value || 0)}%` }} />
    </div>
  )
}

export const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
