import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Alert, PageHeader } from '../components/ui.jsx'

const empty = { student_id: '', name: '', roll_no: '', course: 'MCA', semester: 1, division: 'A', email: '', contact: '', consent: false }

export default function StudentForm() {
  const [f, setF] = useState(empty)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      const s = await api('/api/students', { method: 'POST', body: { ...f, semester: Number(f.semester) || 1 } })
      navigate(`/students/${s.id}/face`)
    } catch (ex) { setErr(ex.message) } finally { setBusy(false) }
  }

  // plain function (not a component) so inputs keep focus while typing
  const field = (k, label, p = {}) => (
    <div key={k}><label className="label" htmlFor={k}>{label}</label>
      <input id={k} className="input" value={f[k]} onChange={set(k)} {...p} /></div>
  )

  return (
    <>
      <PageHeader title="Register student" subtitle="Step 1 of 2 · Details. Next you will capture the face." />
      <form onSubmit={submit} className="card p-6 max-w-2xl space-y-4">
        <Alert>{err}</Alert>
        <div className="grid sm:grid-cols-2 gap-4">
          {field("name", "Full name", { required: true })}
          {field("roll_no", "Roll number", { required: true, placeholder: "MCA001" })}
          {field("student_id", "PRN / Student ID", { required: true })}
          {field("course", "Course")}
          {field("semester", "Semester", { type: "number", min: 1, max: 8 })}
          {field("division", "Division")}
          {field("email", "Email", { type: "email" })}
          {field("contact", "Contact number")}
        </div>
        <label className="flex gap-3 items-start rounded-md bg-brand-tint p-3 text-sm">
          <input type="checkbox" className="mt-1" checked={f.consent} onChange={set('consent')} />
          <span>The student has given consent for their face data (mathematical face embeddings, not photos) to be
            stored and used only for attendance. They can ask for it to be deleted at any time.</span>
        </label>
        <button className="btn-primary" disabled={busy || !f.consent}>{busy ? 'Saving…' : 'Save & capture face'}</button>
      </form>
    </>
  )
}
