import { useCallback, useEffect, useRef, useState } from 'react'

export default function useCamera() {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [active, setActive] = useState(false)
  const [error, setError] = useState('')

  const start = useCallback(async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 960 }, height: { ideal: 540 }, facingMode: 'user' }, audio: false })
      streamRef.current = stream
      if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play() }
      setActive(true)
    } catch (e) {
      setError(e.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow camera access in the browser address bar.'
        : 'No camera found or it is being used by another app.')
    }
  }, [])

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setActive(false)
  }, [])

  // returns a JPEG data URL of the current frame (null if camera not ready)
  const capture = useCallback((width = 480, quality = 0.8) => {
    const v = videoRef.current
    if (!v || !v.videoWidth) return null
    const c = document.createElement('canvas')
    c.width = width
    c.height = Math.round((v.videoHeight / v.videoWidth) * width)
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height)
    return c.toDataURL('image/jpeg', quality)
  }, [])

  useEffect(() => stop, [stop])
  return { videoRef, active, error, start, stop, capture }
}
