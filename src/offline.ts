const OFFLINE_KEY = 'walk-listen-offline-ids'

export function getOfflineIds(): Set<string> {
  try {
    const raw = localStorage.getItem(OFFLINE_KEY)
    if (!raw) return new Set()
    return new Set(JSON.parse(raw) as string[])
  } catch {
    return new Set()
  }
}

function saveOfflineIds(ids: Set<string>) {
  localStorage.setItem(OFFLINE_KEY, JSON.stringify([...ids]))
}

export function markOffline(id: string) {
  const ids = getOfflineIds()
  ids.add(id)
  saveOfflineIds(ids)
}

export function unmarkOffline(id: string) {
  const ids = getOfflineIds()
  ids.delete(id)
  saveOfflineIds(ids)
}

/** 主动把音频写入 Cache，保证断网可播 */
export async function cacheEpisodeAudio(id: string, audioUrl: string): Promise<void> {
  const cache = await caches.open('walk-listen-audio')
  const res = await fetch(audioUrl)
  if (!res.ok) throw new Error(`下载失败: ${res.status}`)
  await cache.put(audioUrl, res.clone())
  markOffline(id)
}

export async function removeCachedAudio(id: string, audioUrl: string): Promise<void> {
  const cache = await caches.open('walk-listen-audio')
  await cache.delete(audioUrl)
  unmarkOffline(id)
}

export async function isAudioCached(audioUrl: string): Promise<boolean> {
  const cache = await caches.open('walk-listen-audio')
  const hit = await cache.match(audioUrl)
  return Boolean(hit)
}
