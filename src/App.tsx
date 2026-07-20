import { useCallback, useEffect, useState } from 'react'
import type { Catalog, Episode } from './types'
import { cacheEpisodeAudio, getOfflineIds, isAudioCached, removeCachedAudio } from './offline'
import { usePlayer } from './usePlayer'
import './App.css'

export default function App() {
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [offlineIds, setOfflineIds] = useState<Set<string>>(() => getOfflineIds())
  const [busyId, setBusyId] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [online, setOnline] = useState(navigator.onLine)
  const [showHelp, setShowHelp] = useState(false)
  const player = usePlayer()

  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const catalogUrl = `${import.meta.env.BASE_URL}catalog.json`
        const res = await fetch(catalogUrl, { cache: 'no-cache' })
        if (!res.ok) throw new Error(String(res.status))
        const data = (await res.json()) as Catalog
        if (cancelled) return
        setEpisodes(data.episodes ?? [])
        setLoadError(null)

        const next = new Set(getOfflineIds())
        await Promise.all(
          (data.episodes ?? []).map(async (ep) => {
            const url = ep.audio.startsWith('http')
              ? ep.audio
              : `${import.meta.env.BASE_URL}${ep.audio.replace(/^\//, '')}`
            if (await isAudioCached(url)) next.add(ep.id)
          }),
        )
        if (!cancelled) setOfflineIds(next)
      } catch {
        if (!cancelled) setLoadError('暂时读不到节目列表。若已离线，请确认之前打开过本页。')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const audioUrl = useCallback((ep: Episode) => {
    if (ep.audio.startsWith('http')) return ep.audio
    return `${import.meta.env.BASE_URL}${ep.audio.replace(/^\//, '')}`
  }, [])

  const onDownload = useCallback(async (ep: Episode) => {
    setBusyId(ep.id)
    try {
      await cacheEpisodeAudio(ep.id, audioUrl(ep))
      setOfflineIds(new Set(getOfflineIds()))
    } catch {
      alert('下载失败，请检查网络后重试')
    } finally {
      setBusyId(null)
    }
  }, [audioUrl])

  const onRemove = useCallback(async (ep: Episode) => {
    setBusyId(ep.id)
    try {
      await removeCachedAudio(ep.id, audioUrl(ep))
      setOfflineIds(new Set(getOfflineIds()))
    } finally {
      setBusyId(null)
    }
  }, [audioUrl])

  const progress =
    player.duration > 0 ? Math.min(1, player.currentTime / player.duration) : 0

  return (
    <div className="app">
      <div className="atmosphere" aria-hidden />

      <header className="hero">
        <p className="brand">走路听</p>
        <h1 className="tagline">插上耳机，边走边听</h1>
        <p className="lede">
          中文知识，离线可播。内容你随时叫我整理，音色走好听路线。
        </p>
        <p className={`net ${online ? 'on' : 'off'}`}>
          {online ? '当前在线' : '当前离线 · 仅可播放已下载'}
        </p>
      </header>

      <main className="list-wrap">
        <h2 className="section-title">节目</h2>
        {loadError && <p className="hint error">{loadError}</p>}
        {!loadError && episodes.length === 0 && (
          <p className="hint empty">
            还没有节目。内容准备好后，我会写成讲稿、配上好听的中文声音，这里就会出现列表。
          </p>
        )}
        <ul className="episode-list">
          {episodes.map((ep) => {
            const saved = offlineIds.has(ep.id)
            const active = player.episode?.id === ep.id
            return (
              <li key={ep.id} className={`episode ${active ? 'active' : ''}`}>
                <button
                  type="button"
                  className="episode-main"
                  onClick={() => void player.load(ep)}
                >
                  <span className="ep-title">{ep.title}</span>
                  <span className="ep-desc">{ep.description}</span>
                </button>
                <div className="episode-actions">
                  {saved ? (
                    <button
                      type="button"
                      className="chip"
                      disabled={busyId === ep.id}
                      onClick={() => void onRemove(ep)}
                    >
                      已离线 · 移除
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="chip primary"
                      disabled={busyId === ep.id || !online}
                      onClick={() => void onDownload(ep)}
                    >
                      {busyId === ep.id ? '下载中…' : '下载离线'}
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>

        <p className="help-link-wrap">
          <button type="button" className="help-link" onClick={() => setShowHelp(true)}>
            如何更新节目
          </button>
        </p>
      </main>

      {showHelp && (
        <div className="help-overlay" role="dialog" aria-modal="true" aria-labelledby="help-title">
          <div className="help-sheet">
            <h2 id="help-title">如何更新节目</h2>
            <ol className="help-steps">
              <li>跟 Cursor 说你想听什么、用什么口吻。</li>
              <li>
                把讲稿上传到仓库的{' '}
                <a
                  href="https://github.com/i71365689-blip/walk-listen/upload/main/content/episodes"
                  target="_blank"
                  rel="noreferrer"
                >
                  content/episodes
                </a>
                ，或在 GitHub 网页里直接改 .md。
              </li>
              <li>
                打开{' '}
                <a
                  href="https://github.com/i71365689-blip/walk-listen/actions"
                  target="_blank"
                  rel="noreferrer"
                >
                  Actions
                </a>
                ，等「Generate TTS」和「Deploy」跑完。
              </li>
              <li>回到本页刷新，就能听到新节目。</li>
            </ol>
            <p className="help-note">
              不用在电脑开后台、不用监听端口。调音色改讲稿里的 voice / rate / pitch 即可。
            </p>
            <button type="button" className="chip primary" onClick={() => setShowHelp(false)}>
              知道了
            </button>
          </div>
        </div>
      )}

      <footer className={`player ${player.episode ? 'visible' : ''}`}>
        {player.episode && (
          <>
            <div className="now">
              <p className="now-label">正在听</p>
              <p className="now-title">{player.episode.title}</p>
            </div>
            <input
              className="seek"
              type="range"
              min={0}
              max={1}
              step={0.001}
              value={progress}
              aria-label="进度"
              onChange={(e) => player.seek(Number(e.target.value))}
            />
            <div className="times">
              <span>{player.formatTime(player.currentTime)}</span>
              <span>{player.formatTime(player.duration)}</span>
            </div>
            <div className="controls">
              <button type="button" className="ctrl" onClick={() => player.skip(-15)}>
                −15s
              </button>
              <button type="button" className="ctrl play" onClick={() => void player.toggle()}>
                {player.playing ? '暂停' : '播放'}
              </button>
              <button type="button" className="ctrl" onClick={() => player.skip(15)}>
                +15s
              </button>
            </div>
            {player.error && <p className="hint error">{player.error}</p>}
          </>
        )}
      </footer>
    </div>
  )
}
