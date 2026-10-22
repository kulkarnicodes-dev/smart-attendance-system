import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Camera, CircleStop, Download, Lock } from 'lucide-react'
import { api, download } from '../api'
import { useAsync } from '../components/hooks.js'
import useCamera from '../components/useCamera.js'
import { Alert, PageHeader, StatusPill } from '../components/ui.jsx'

const INTERVAL_MS = 1200
const COLORS = { marked: '#1E8E5A', already_marked: '#0E7C7B', unknown: '#C77D0A', uncertain: '#C77D0A', not_enrolled: '#C0392B', too_small: '#6B7F8B' }
const LABEL = { unknown: 'Unknown face: not marked', uncertain: 'Not sure: needs review', not_enrolled: 'Not enrolled in this subject', too_small: 'Move closer' }

export default function SessionRoom() {
  const { id } = useParams()
  const cam = useCamera()
  const { data: s, err, reload, setErr } = useAsync(() => api(`/api/sessions/${id}`), [id])
  const [running, setRunning] = useState(false)
  const [faces, setFaces] = useState([])
  const [review, setReview] = useState({})     // uncertain candidates by student id
  const [info, setInfo] = useState('')
  const busy = useRef(false)
  const timer = useRef(null)
  const open = s?.status === 'open'

  const tick = async () => {
    if (busy.current) return
    const img = cam.capture(480, 0.7)
    if (!img) return
    busy.current = true
    try {
      const r = await api('/api/recognition/identify', { method: 'POST', body: { image: img, session_id: +id } })
      setFaces(r.faces)
      const unc = {}
      r.faces.filter((f) => f.status === 'uncertain' && f.student).forEach((f) => { unc[f.student.id] = f })
      setReview((p) => ({ ...p, ...unc }))
      if (r.faces.some((f) => f.status === 'marked')) reload()
    } catch (e) { setErr(e.message); if (/finalized/.test(e.message)) setRunning(false) } finally { busy.current = false }
  }

  useEffect(() => {
    if (running && cam.active && open) { timer.current = setInterval(tick, INTERVAL_MS); return () => clearInterval(timer.current) }
  }, [running, cam.active, open])

  const start = async () => { if (!cam.active) await cam.start(); setRunning(true) }
  const stop = () => { setRunning(false); setFaces([]); cam.stop() }

  const mark = async (pk, status) => {
    let reason = ''
    const row = s.students.find((x) => x.student_pk === pk)
    if (!open || (row.status && row.method === 'face' && row.status !== status)) {
      reason = prompt('Reason for this change (required, min 5 characters):') || ''
      if (reason.trim().length < 5) return
    }
    try { await api(`/api/sessions/${id}/mark`, { method: 'POST', body: { student_pk: pk, status, reason } }); setReview((p) => { const n = { ...p }; delete n[pk]; return n }); reload() }
    catch (e) { setErr(e.message) }
  }

  const finalize = async () => {
    if (!confirm('Finalize this lecture? The register will be locked.')) return
    try { await api(`/api/sessions/${id}/finalize`, { method: 'POST', body: { confirm_absent: false } }) }
    catch (e) {
      if (!/Confirm to mark/.test(e.message)) return setErr(e.message)
      if (!confirm(`${e.message}\n\nMark the unmarked students Absent and finalize?`)) return
      try { await api(`/api/sessions/${id}/finalize`, { method: 'POST', body: { confirm_absent: true } }) } catch (e2) { return setErr(e2.message) }
    }
    stop(); setInfo('Session finalized and locked.'); reload()
  }

  if (!s) return err ? <Alert>{err}</Alert> : <div className="text-ink-mute">Loading…</div>
  const present = (s.counts.Present || 0) + (s.counts.Late || 0)

  return (
    <>
      <PageHeader title={`${s.subject} · ${s.date} ${s.start}`} subtitle={`Division ${s.division || 'all'} · ${s.teacher}${s.topic ? ' · ' + s.topic : ''}`}>
        <StatusPill status={s.status} />
        <button className="btn-ghost" onClick={() => download(`/api/analytics/export/session/${id}`, `session_${id}.csv`).catch((e) => setErr(e.message))}><Download size={16} /> CSV</button>
        <Link to="/sessions" className="btn-ghost">Back</Link>
      </PageHeader>
      <Alert>{cam.error || err}</Alert>
      <Alert kind="ok">{info}</Alert>

      <div className="grid lg:grid-cols-5 gap-5">
        <div className="lg:col-span-3 space-y-3">
          {open ? (
            <>
              <div className="card overflow-hidden bg-ink relative aspect-video">
                <video ref={cam.videoRef} muted playsInline className="w-full h-full object-cover -scale-x-100" />
                {!cam.active && <div className="absolute inset-0 grid place-items-center text-white/70 text-sm">Start face attendance to open the camera</div>}
                {faces.map((f, i) => {
                  const [x, y, w, h] = f.box
                  const text = f.student && (f.status === 'marked' || f.status === 'already_marked') ? `${f.student.name} · ${f.status === 'marked' ? f.value : 'Already marked'}`
                    : f.student ? `${f.student.name}? ${LABEL[f.status]}` : LABEL[f.status]
                  return (
                    <div key={i} className="absolute border-2 rounded" style={{ left: `${(1 - x - w) * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%`, borderColor: COLORS[f.status] }}>
                      <span className="absolute -top-6 left-0 whitespace-nowrap rounded px-1.5 py-0.5 text-xs font-semibold text-white" style={{ background: COLORS[f.status] }}>{text}</span>
                    </div>)
                })}
              </div>
              <div className="flex flex-wrap gap-2">
                {!running ? <button className="btn-primary" onClick={start}><Camera size={16} /> Start face attendance</button>
                  : <button className="btn-danger" onClick={stop}><CircleStop size={16} /> Stop camera</button>}
                <button className="btn-primary !bg-ink hover:!bg-ink-soft" onClick={finalize}><Lock size={16} /> Finalize & lock</button>
              </div>
              {Object.keys(review).length > 0 && (
                <div className="card p-4"><h3 className="font-semibold text-sm mb-2">Needs your review (uncertain matches)</h3>
                  {Object.values(review).map((f) => (
                    <div key={f.student.id} className="flex items-center justify-between text-sm py-1.5 border-t border-paper-line">
                      <span>Looks like <b>{f.student.name}</b> ({Math.round(f.confidence * 100)}% match)</span>
                      <button className="btn-ghost !py-1" onClick={() => mark(f.student.id, 'Present')}>Confirm present</button></div>))}
                </div>)}
            </>
          ) : <div className="card p-5 text-sm text-ink-soft">This lecture is finalized and locked. Changes now require a reason and are written to the audit log.</div>}
        </div>

        <section className="lg:col-span-2 card">
          <div className="p-4 pb-2 flex justify-between"><h2 className="font-semibold">Roster</h2>
            <span className="text-sm text-ink-mute">{present} present · {s.unmarked} unmarked · {s.roster} total</span></div>
          {s.students.length === 0 && <p className="p-4 text-sm text-ink-mute">No students are enrolled in this subject/division. Ask an admin to enroll students.</p>}
          <ul className="max-h-[520px] overflow-y-auto">
            {s.students.map((st) => (
              <li key={st.student_pk} className="flex items-center justify-between gap-2 px-4 py-2 border-t border-paper-line text-sm">
                <div className="min-w-0"><div className="font-medium truncate">{st.name}</div>
                  <div className="text-xs text-ink-mute">{st.roll_no}{st.time ? ` · ${st.time.slice(0, 5)}` : ''}{st.method ? ` · ${st.method}` : ''}{st.face_count === 0 ? ' · no face data' : ''}</div></div>
                <div className="flex items-center gap-2 shrink-0"><StatusPill status={st.status} />
                  <select aria-label={`Mark ${st.name}`} className="input !w-24 !py-1 !text-xs" value="" onChange={(e) => e.target.value && mark(st.student_pk, e.target.value)}>
                    <option value="">Mark…</option>{['Present', 'Late', 'Absent', 'Excused'].map((x) => <option key={x}>{x}</option>)}</select></div>
              </li>))}
          </ul>
        </section>
      </div>
    </>
  )
}
