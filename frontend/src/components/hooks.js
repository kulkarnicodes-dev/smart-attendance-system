import { useCallback, useEffect, useState } from 'react'

// load data on mount / when deps change; returns {data, err, reload, setErr}
export function useAsync(fn, deps = []) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const reload = useCallback(() => fn().then((d) => { setData(d); setErr('') }).catch((e) => setErr(e.message)), deps) // eslint-disable-line
  useEffect(() => { reload() }, [reload])
  return { data, err, reload, setErr }
}
