import { createContext, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!getToken())

  useEffect(() => {
    if (!getToken()) return
    api('/api/auth/me').then(setUser).catch(() => setToken(null)).finally(() => setLoading(false))
  }, [])

  const login = async (username, password) => {
    const r = await api('/api/auth/login', { method: 'POST', body: { username, password } })
    setToken(r.access_token)
    setUser(r.user)
  }
  const logout = () => { setToken(null); setUser(null) }

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>
}
