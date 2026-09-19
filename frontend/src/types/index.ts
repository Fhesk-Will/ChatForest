export interface CardPosition {
  x: number
  y: number
}

export type CardStatus = 'idle' | 'streaming' | 'done' | 'error'

export interface Card {
  id: string
  position: CardPosition
  user_message: string
  ai_message: string
  model_id: string
  status: CardStatus
  created_at: string
  is_summary?: boolean
  summarized_card_ids?: string[]
  is_suppressed?: boolean
}

export interface Edge {
  id: string
  source: string
  target: string
}

export interface Canvas {
  id: string
  title: string
  created_at: string
  updated_at: string
  cards: Card[]
  edges: Edge[]
}

export interface CanvasSummary {
  id: string
  title: string
  updated_at: string
}

export interface Provider {
  id: string
  name: string
  type: string
  base_url: string
  api_key: string
  models: string[]
  context_limit?: number
}

export interface DefaultModel {
  provider_id: string
  model: string
}

export interface ModelsConfig {
  providers: Provider[]
  default_model: DefaultModel
  summary_model?: DefaultModel
  auto_summary_threshold?: number
  auto_summary_keep_recent?: number
  summary_prompt?: string
}

export interface SummarizeRequest {
  canvas_id: string
  up_to_card_id: string
  provider_id?: string
  model?: string
}

export interface SummarizeResponse {
  summary: string
  summarized_card_ids: string[]
}

export interface ChatRequest {
  canvas_id: string
  parent_card_id: string | null
  user_message: string
  provider_id?: string
  model?: string
}
