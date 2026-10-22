import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth.jsx'
import { useAsync } from '../components/hooks.js'
import { Alert, Empty, PageHeader, StatusPill } from '../components/ui.jsx'

export default function Users() {
  const { user: me } = useAuth()
  const [role, setRole] = useState('')
  const users = useAsync(() => api(`/api/admin/users${role ? `?role=${role}` : ''}`), [role])
  const [msg, setMsg] = useState({ kind: 'ok', text: '' })
  const [show, setShow] = useState(false)
  const [f, setF] = useState({ username: '', password: '', full_name: '', email: '', department: 'MCA', role: 'teacher' })
  const act = async (fn, ok) => { try { const r = await fn(); setMsg({ kind: 'ok', text: typeof ok === 'function' ? ok(r) : ok }); users.reload() } catch (e) { setMsg({ kind: 'error', text: e.message }) } }
  const post = (p, body) => api(p, { method: 'POST', body })

  return (
    <>
      <PageHeader title="Users" subtitle="Approve students, create teachers, reset passwords">
        <select className="input !w-36" value={role} onChange={(e) => setRole(e.target.value)} aria-label="Filter by role">
          <option value="">All roles</option><option value="student">Students</option><option value="teacher">Teachers</option><option value="admin">Admins</option></select>
        <button className="btn-primary" onClick={() => setShow(!show)}>Add teacher/admin</button>
      </PageHeader>
      <Alert kind={msg.kind}>{msg.text}</Alert>
      {show && (
        <form className="card p-5 mb-5 grid sm:grid-cols-3 gap-3" onSubmit={(e) => { e.preventDefault(); act(() => post('/api/admin/users', f), 'User created. They must change the password at first login.') }}>
          {['full_name', 'username', 'email', 'department'].map((k) => <div key={k}><label className="label capitalize">{k.replace('_', ' ')}</label>
            <input className="input" value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} required={k !== 'email' && k !== 'department'} /></div>)}
          <div><label className="label">Temporary password</label><input className="input" type="password" minLength={6} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></div>
          <div><label className="label">Role</label><select className="input" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option>teacher</option><option>admin</option></select></div>
          <div className="sm:col-span-3"><button className="btn-primary">Create</button></div>
        </form>)}
      <div className="card overflow-x-auto">
        {!users.data ? <Empty>Loading…</Empty> : (
          <table className="w-full"><thead><tr>{['Name', 'Username', 'Role', 'Status', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody>{users.data.map((u) => (
              <tr key={u.id}><td className="td font-medium">{u.full_name || '-'}<div className="text-xs text-ink-mute">{u.email}</div></td>
                <td className="td">{u.username}</td><td className="td capitalize">{u.role}</td><td className="td"><StatusPill status={u.status} /></td>
                <td className="td"><div className="flex gap-2 justify-end flex-wrap">
                  {u.status === 'pending' && <button className="btn-primary !py-1" onClick={() => act(() => post(`/api/admin/users/${u.id}/approve`), 'Account approved')}>Approve</button>}
                  {u.id !== me.id && u.status !== 'pending' && <button className="btn-ghost !py-1" onClick={() => act(() => post(`/api/admin/users/${u.id}/status`, { status: u.status === 'active' ? 'disabled' : 'active' }), 'Status updated')}>{u.status === 'active' ? 'Disable' : 'Enable'}</button>}
                  <button className="btn-ghost !py-1" onClick={() => confirm(`Reset password for ${u.username}?`) && act(() => post(`/api/admin/users/${u.id}/reset-password`), (r) => `Temporary password for ${u.username}: ${r.temporary_password} (shown once; user must change it at next login)`)}>Reset password</button>
                </div></td></tr>))}</tbody></table>)}
      </div>
    </>
  )
}
