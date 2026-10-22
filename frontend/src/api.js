const BASE = import.meta.env.VITE_API_URL || ''

export const getToken = () => localStorage.getItem('sa_token')
export const setToken = (t) => (t ? localStorage.setItem('sa_token', t) : localStorage.removeItem('sa_token'))

export async function api(path, { method = 'GET', body, blob = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new Error('Cannot reach the server. Is the backend running on port 8000?')
  }
  if (res.status === 401 && !path.includes('/auth/login')) {
    setToken(null)
    window.location.href = '/login'
    throw new Error('Session expired')
  }
  if (!res.ok) {
    let msg = res.statusText
    try {
      const j = await res.json()
      msg = typeof j.detail === 'string' ? j.detail : j.detail?.[0]?.msg || msg
    } catch {}
    throw new Error(msg)
  }
  return blob ? res.blob() : res.json()
}

export async function download(path, filename) {
  const blob = await api(path, { blob: true })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
}

export const qs = (obj) => {
  const p = new URLSearchParams()
  Object.entries(obj).forEach(([k, v]) => v !== '' && v != null && p.append(k, v))
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const today = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
