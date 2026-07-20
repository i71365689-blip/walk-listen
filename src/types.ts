export type Episode = {
  id: string
  title: string
  description: string
  audio: string
  script?: string
  voice?: string
  durationHint?: string
}

export type Catalog = {
  episodes: Episode[]
}
