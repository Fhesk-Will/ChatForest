import type { Canvas, CanvasSummary, ModelsConfig, SummarizeRequest, SummarizeResponse } from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}

export const api = {
  // Canvas
  listCanvases: () => request<CanvasSummary[]>('/canvases'),
  createCanvas: (title?: string) =>
    request<Canvas>('/canvases', { method: 'POST', body: JSON.stringify({ title }) }),
  getCanvas: (id: string) => request<Canvas>(`/canvases/${id}`),
  saveCanvas: (id: string, canvas: Canvas) =>
    request<Canvas>(`/canvases/${id}`, { method: 'PUT', body: JSON.stringify(canvas) }),
  deleteCanvas: (id: string) =>
    request<{ ok: boolean }>(`/canvases/${id}`, { method: 'DELETE' }),
  summarizeTitle: (id: string, userMessage: string) =>
    request<{ title: string }>(`/canvases/${id}/summarize-title`, {
      method: 'POST',
      body: JSON.stringify({ user_message: userMessage }),
    }),

  // Models
  getModels: () => request<ModelsConfig>('/models'),
  saveModels: (config: ModelsConfig) =>
    request<{ ok: boolean }>('/models', { method: 'PUT', body: JSON.stringify(config) }),

  // Summarize conversation
  summarize: (payload: SummarizeRequest) =>
    request<SummarizeResponse>('/chat/summarize', { method: 'POST', body: JSON.stringify(payload) }),

  // Chat stream — returns a ReadableStream reader
  chatStream: async (
    payload: {
      canvas_id: string
      parent_card_id: string | null
      user_message: string
      provider_id?: string
      model?: string
    },
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (msg: string) => void,
    onSummary?: (summary: string, summarizedCardIds: string[]) => void,
  ) => {
    const res = await fetch(`${BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok || !res.body) {
      onError(`HTTP ${res.status}`)
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') { onDone(); return }
        if (data.startsWith('[ERROR]')) { onError(data.slice(8)); return }
        if (data.startsWith('[SUMMARY] ')) {
          try {
            const parsed = JSON.parse(data.slice(10))
            onSummary?.(parsed.summary, parsed.summarized_card_ids)
          } catch { /* 忽略格式错误 */ }
          continue
        }
        // Decode escaped newlines and backslashes
        onToken(data.replace(/\\n/g, '\n').replace(/\\\\/g, '\\'))
      }
    }
    onDone()
  },
}
