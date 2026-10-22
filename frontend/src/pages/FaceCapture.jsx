import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { Camera, RotateCcw } from 'lucide-react'
import { api } from '../api'
import useCamera from '../components/useCamera.js'
import { Alert, PageHeader } from '../components/ui.jsx'

const TARGET = 20
const PROMPTS = ['Look straight at the camera', 'Turn slightly left', 'Turn slightly right', 'Tilt chin up a little', 'Smile / neutral expression']

export default function FaceCapture() {
  const { id: pid } = useParams()
  const { user } = useAuth()
  const [id, setId] = useState(pid)
  const cam = useCamera()
  const [student, setStudent] = useState(null)
  const [count, setCount] = useState(0)
  const [running, setRunning] = useState(false)
  const [msg, setMsg] = useState({ kind: 'warn', text: '' })
  const stopRef = useRef(false)

  useEffect(() => {
    if (!pid) api('/api/students/me').then((s) => setId(s.id)).catch((e) => setMsg({ kind: 'error', text: e.message }))
  }, [pid])

  useEffect(() => {
    if (!id) return
    api(`/api/students/${id}`).then((s) => { setStudent(s); setCount(s.face_count) })
      .catch((e) => setMsg({ kind: 'error', text: e.message }))
  }, [id])

  const run = async () => {
    setRunning(true); stopRef.current = false; setMsg({ kind: 'warn', text: '' })
    let n = count, fails = 0
    while (n < TARGET && !stopRef.current && fails < 8) {
      const img = cam.capture(480, 0.85)
      if (!img) { await sleep(300); continue }
      try {
        const r = await api(`/api/students/${id}/face`, { method: 'POST', body: { image: img } })
        n = r.face_count; setCount(n); fails = 0
        await sleep(650)  // give the student time to move slightly between samples
      } catch (e) {
        fails++
        setMsg({ kind: 'warn', text: e.message })
        if (e.message.includes('Maximum') || e.message.includes('models')) break
        await sleep(600)
      }
    }
    setRunning(false)
    if (n >= TARGET) setMsg({ kind: 'ok', text: `Done. ${n} face samples saved. Face attendance can now recognise this student.` })
    else if (fails >= 8) setMsg({ kind: 'error', text: 'Too many failed attempts. Check lighting and that only one face is visible.' })
  }

  const reset = async () => {
    if (!confirm('Delete all captured face samples for this student?')) return
    await api(`/api/students/${id}/face`, { method: 'DELETE' }); setCount(0)
  }

  const pct = Math.min(100, Math.round((count / TARGET) * 100))
  const prompt = PROMPTS[Math.min(PROMPTS.length - 1, Math.floor((count / TARGET) * PROMPTS.length))]

  return (
    <>
      <PageHeader title={student ? (user.role === 'student' ? 'My face data' : `Capture face: ${student.name}`) : 'Capture face'} subtitle={`Step 2 of 2 · ${student?.roll_no ?? ''}`}>
        <Link to={user.role === 'student' ? '/' : '/students'} className="btn-ghost">Back</Link>
      </PageHeader>
      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-3">
          <div className="card overflow-hidden bg-ink relative aspect-video">
            <video ref={cam.videoRef} muted playsInline className="w-full h-full object-cover -scale-x-100" />
            {!cam.active && <div className="absolute inset-0 grid place-items-center text-white/70 text-sm">Camera is off</div>}
            {running && <div className="absolute bottom-3 left-3 right-3 rounded-md bg-black/60 px-3 py-2 text-white text-sm">{prompt}</div>}
          </div>
          <Alert kind="error">{cam.error}</Alert>
          <Alert kind={msg.kind}>{msg.text}</Alert>
        </div>
        <div className="card p-5 space-y-4 h-fit">
          <div>
            <div className="flex justify-between text-sm mb-1"><span>Face samples</span><b>{count} / {TARGET}</b></div>
            <div className="h-2 rounded bg-paper"><div className="h-2 rounded bg-brand transition-all" style={{ width: `${pct}%` }} /></div>
          </div>
          <ul className="text-sm text-ink-soft list-disc pl-5 space-y-1">
            <li>Sit in good, even light</li>
            <li>Only one person in the frame</li>
            <li>Move your head slightly between captures</li>
            <li>Remove cap or mask for registration</li>
          </ul>
          {!cam.active
            ? <button className="btn-primary w-full" onClick={cam.start}><Camera size={16} /> Turn on camera</button>
            : !running
              ? <button className="btn-primary w-full" onClick={run} disabled={count >= TARGET}>{count > 0 && count < TARGET ? 'Continue capture' : 'Start capture'}</button>
              : <button className="btn-ghost w-full" onClick={() => { stopRef.current = true }}>Pause</button>}
          {cam.active && <button className="btn-ghost w-full" onClick={cam.stop} disabled={running}>Turn off camera</button>}
          {count > 0 && <button className="btn-danger w-full" onClick={reset} disabled={running}><RotateCcw size={15} /> Reset samples</button>}
        </div>
      </div>
    </>
  )
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
