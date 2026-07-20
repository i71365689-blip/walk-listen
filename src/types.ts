export type Episode = {
  id: string
  title: string
  description: string
  audio: string
  script?: string
  voice?: string
  rate?: string
  pitch?: string
  tone?: string
  durationHint?: string
}

export type Catalog = {
  episodes: Episode[]
}
