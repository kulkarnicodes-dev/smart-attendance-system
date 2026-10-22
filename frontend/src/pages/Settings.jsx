import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth.jsx'
import { Alert, PageHeader } from '../components/ui.jsx'

export default function Settings() {
  const { user } = useAuth()
  const [health, setHealth] = useState(null)
  const [pw, setPw] = useState({ old_password: '', new_password: '' })
  const [msg, setMsg] = useState({ kind: 'ok', text: '' })
  const [cfg, setCfg] = useState(null)
  const [cfgMsg, setCfgMsg] = useState({ kind: 'ok', text: '' })

  useEffect(() => {
    api('/api/health').then(setHealth).catch(() => setHealth({ status: 'down' }))
    api('/api/admin/settings').then(setCfg).catch(() => {})
  }, [])

  const change = async (e) => {
    e.preventDefault()
    try { await api('/api/auth/change-password', { method: 'POST', body: pw }); setMsg({ kind: 'ok', text: 'Password updated.' }); setPw({ old_password: '', new_password: '' }) }
    catch (ex) { setMsg({ kind: 'error', text: ex.message }) }
  }
  const saveCfg = async (e) => {
    e.preventDefault()
    try { await api('/api/admin/settings', { method: 'PUT', body: { threshold: +cfg.threshold, late_after_min: +cfg.late_after_min } }); setCfgMsg({ kind: 'ok', text: 'Saved.' }) }
    catch (ex) { setCfgMsg({ kind: 'error', text: ex.message }) }
  }

  return (
    <>
      <PageHeader title="Settings" subtitle={`Signed in as ${user.username} (${user.role})`} />
      {user.must_change_password && <Alert kind="warn">Your password was set by an administrator. Please choose a new one now.</Alert>}
      <div className="grid md:grid-cols-2 gap-5">
        <form onSubmit={change} className="card p-5 space-y-3">
          <h2 className="font-semibold">Change password</h2>
          <Alert kind={msg.kind}>{msg.text}</Alert>
          <div><label className="label">Current password</label><input type="password" className="input" value={pw.old_password} onChange={(e) => setPw({ ...pw, old_password: e.target.value })} required /></div>
          <div><label className="label">New password (min 6)</label><input type="password" className="input" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} minLength={6} required /></div>
          <button className="btn-primary">Update password</button>
        </form>

        {user.role === 'admin' && cfg && (
          <form onSubmit={saveCfg} className="card p-5 space-y-3">
            <h2 className="font-semibold">Attendance rules</h2>
            <Alert kind={cfgMsg.kind}>{cfgMsg.text}</Alert>
            <div><label className="label">Minimum attendance % (alerts below this)</label><input type="number" className="input" min={1} max={100} value={cfg.threshold} onChange={(e) => setCfg({ ...cfg, threshold: e.target.value })} /></div>
            <div><label className="label">Mark "Late" after (minutes from start)</label><input type="number" className="input" min={0} max={120} value={cfg.late_after_min} onChange={(e) => setCfg({ ...cfg, late_after_min: e.target.value })} /></div>
            <button className="btn-primary">Save rules</button>
          </form>)}

        <section className="card p-5 space-y-2 text-sm md:col-span-2">
          <h2 className="font-semibold">System status</h2>
          {!health ? 'Checking…' : (<>
            <p>Backend: <b className={health.status === 'ok' ? 'text-signal-green' : 'text-signal-red'}>{health.status === 'ok' ? `Running (v${health.version})` : 'Not reachable'}</b></p>
            {health.status === 'ok' && <>
              <p>Face models: <b className={health.models_ready ? 'text-signal-green' : 'text-signal-red'}>{health.models_ready ? 'Ready' : 'Missing, run scripts/download_models.py'}</b></p>
              <p>Match threshold: <b>{health.match_threshold}</b> <span className="text-ink-mute">(MATCH_THRESHOLD in backend/.env)</span></p></>}
          </>)}
        </section>
      </div>
    </>
  )
}
