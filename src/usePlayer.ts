import { useCallback, useEffect, useRef, useState } from 'react'
import type { Episode } from './types'

function formatTime(sec: number) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function usePlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [episode, setEpisode] = useState<Episode | null>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const audio = new Audio()
    audio.preload = 'metadata'
    audioRef.current = audio

    const onTime = () => setCurrentTime(audio.currentTime)
    const onMeta = () => setDuration(audio.duration || 0)
    const onPlay = () => setPlaying(true)
    const onPause = () => setPlaying(false)
    const onEnded = () => setPlaying(false)
    const onErr = () => setError('播放失败，请检查是否已下载或网络是否可用')

    audio.addEventListener('timeupdate', onTime)
    audio.addEventListener('loadedmetadata', onMeta)
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('ended', onEnded)
    audio.addEventListener('error', onErr)

    return () => {
      audio.pause()
      audio.removeEventListener('timeupdate', onTime)
      audio.removeEventListener('loadedmetadata', onMeta)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('ended', onEnded)
      audio.removeEventListener('error', onErr)
      audioRef.current = null
    }
  }, [])

  const syncMediaSession = useCallback((ep: Episode, isPlaying: boolean) => {
    if (!('mediaSession' in navigator)) return
    navigator.mediaSession.metadata = new MediaMetadata({
      title: ep.title,
      artist: '走路听',
      album: '走路听 · 知识',
    })
    navigator.mediaSession.playbackState = isPlaying ? 'playing' : 'paused'
  }, [])

  useEffect(() => {
    if (!('mediaSession' in navigator) || !audioRef.current) return
    const audio = audioRef.current

    navigator.mediaSession.setActionHandler('play', () => void audio.play())
    navigator.mediaSession.setActionHandler('pause', () => audio.pause())
    navigator.mediaSession.setActionHandler('seekbackward', (d) => {
      audio.currentTime = Math.max(0, audio.currentTime - (d.seekOffset ?? 15))
    })
    navigator.mediaSession.setActionHandler('seekforward', (d) => {
      audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + (d.seekOffset ?? 15))
    })
    navigator.mediaSession.setActionHandler('previoustrack', () => {
      audio.currentTime = 0
    })

    return () => {
      navigator.mediaSession.setActionHandler('play', null)
      navigator.mediaSession.setActionHandler('pause', null)
      navigator.mediaSession.setActionHandler('seekbackward', null)
      navigator.mediaSession.setActionHandler('seekforward', null)
      navigator.mediaSession.setActionHandler('previoustrack', null)
    }
  }, [])

  const load = useCallback(
    async (ep: Episode, autoplay = true) => {
      const audio = audioRef.current
      if (!audio) return
      setError(null)
      setEpisode(ep)
      setCurrentTime(0)
      setDuration(0)
      const src = ep.audio.startsWith('http')
        ? ep.audio
        : `${import.meta.env.BASE_URL}${ep.audio.replace(/^\//, '')}`
      audio.src = src
      audio.load()
      syncMediaSession(ep, false)
      if (autoplay) {
        try {
          await audio.play()
          syncMediaSession(ep, true)
        } catch {
          setError('需要点一下播放（浏览器限制自动播放）')
        }
      }
    },
    [syncMediaSession],
  )

  const toggle = useCallback(async () => {
    const audio = audioRef.current
    if (!audio || !episode) return
    if (audio.paused) {
      try {
        await audio.play()
        syncMediaSession(episode, true)
      } catch {
        setError('无法播放，请重试')
      }
    } else {
      audio.pause()
      syncMediaSession(episode, false)
    }
  }, [episode, syncMediaSession])

  const seek = useCallback((ratio: number) => {
    const audio = audioRef.current
    if (!audio || !duration) return
    audio.currentTime = Math.min(duration, Math.max(0, ratio * duration))
  }, [duration])

  const skip = useCallback((delta: number) => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = Math.min(
      audio.duration || Infinity,
      Math.max(0, audio.currentTime + delta),
    )
  }, [])

  return {
    episode,
    playing,
    currentTime,
    duration,
    error,
    load,
    toggle,
    seek,
    skip,
    formatTime,
  }
}
