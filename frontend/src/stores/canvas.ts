import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Canvas, Card, Edge } from '../types'
import { api } from '../api'

function cardToNode(card: Card): any {
  return {
    id: card.id,
    type: 'card',
    position: card.position,
    data: {
      user_message: card.user_message,
      ai_message: card.ai_message,
      model_id: card.model_id,
      status: card.status,
      created_at: card.created_at,
      is_summary: card.is_summary,
      summarized_card_ids: card.summarized_card_ids,
      is_suppressed: card.is_suppressed,
    },
  }
}

function edgeToFlow(edge: Edge): any {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    animated: false,
  }
}

export const useCanvasStore = defineStore('canvas', () => {
  const currentCanvas = ref<Canvas | null>(null)
  const nodes = ref<any[]>([])
  const edges = ref<any[]>([])
  const saving = ref(false)

  let saveTimer: ReturnType<typeof setTimeout> | null = null

  function loadCanvas(canvas: Canvas) {
    currentCanvas.value = canvas
    nodes.value = canvas.cards.map((card) => {
      const node = cardToNode(card)
      // 加载时不可能有正在进行的流，修正残留的 streaming 状态
      if (node.data.status === 'streaming') {
        node.data = { ...node.data, status: 'done' }
      }
      return node
    })
    edges.value = canvas.edges.map(edgeToFlow)
  }

  function scheduleSave() {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => persistCanvas(), 1000)
  }

  async function persistCanvas() {
    if (!currentCanvas.value) return
    saving.value = true
    try {
      const canvas = buildCanvasPayload()
      await api.saveCanvas(canvas.id, canvas)
      currentCanvas.value = canvas
    } finally {
      saving.value = false
    }
  }

  function buildCanvasPayload(): Canvas {
    const base = currentCanvas.value!
    const cards: Canvas['cards'] = (nodes.value as any[]).map((n) => ({
      id: n.id,
      position: n.position,
      user_message: n.data.user_message,
      ai_message: n.data.ai_message,
      model_id: n.data.model_id,
      status: n.data.status as Canvas['cards'][0]['status'],
      created_at: n.data.created_at,
      is_summary: n.data.is_summary,
      summarized_card_ids: n.data.summarized_card_ids,
      is_suppressed: n.data.is_suppressed,
    }))
    const edgeList: Canvas['edges'] = (edges.value as any[]).map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
    }))
    return { ...base, cards, edges: edgeList }
  }

  function updateNodePosition(id: string, position: { x: number; y: number }) {
    const node = nodes.value.find((n) => n.id === id)
    if (node) {
      node.position = position
      scheduleSave()
    }
  }

  function addEdge(source: string, target: string) {
    const id = `edge_${Date.now()}`
    edges.value.push({ id, source, target, type: 'smoothstep', animated: false })
    scheduleSave()
  }

  function removeEdge(edgeId: string) {
    edges.value = edges.value.filter((e) => e.id !== edgeId)
    scheduleSave()
  }

  function refreshSuppression(branchPointId: string) {
    const parentNode = nodes.value.find((n) => n.id === branchPointId)
    if (!parentNode?.data.is_suppressed) return

    const summaryNode = nodes.value.find(
      (n) => n.data.is_summary && n.data.summarized_card_ids?.includes(branchPointId),
    )
    if (!summaryNode) {
      parentNode.data = { ...parentNode.data, is_suppressed: false }
      scheduleSave()
      return
    }

    const summarizedIds: string[] = summaryNode.data.summarized_card_ids
    const exclusive = new Set(findExclusiveNodes(summarizedIds))
    for (const cid of summarizedIds) {
      const node = nodes.value.find((n) => n.id === cid)
      if (!node) continue
      const shouldSuppress = exclusive.has(cid)
      if (node.data.is_suppressed !== shouldSuppress) {
        node.data = { ...node.data, is_suppressed: shouldSuppress }
      }
    }
    scheduleSave()
  }

  function addCard(userMessage: string, parentId: string | null, position?: { x: number; y: number }, extraData?: Record<string, unknown>): string {
    const id = `card_${Date.now()}`
    const pos = position ?? { x: 200 + Math.random() * 200, y: 100 + nodes.value.length * 220 }
    nodes.value.push({
      id,
      type: 'card',
      position: pos,
      data: {
        user_message: userMessage,
        ai_message: '',
        model_id: '',
        status: 'streaming',
        created_at: new Date().toISOString(),
        ...extraData,
      },
    })
    if (parentId) {
      addEdge(parentId, id)
      refreshSuppression(parentId)
    }
    return id
  }

  function updateCardAiMessage(cardId: string, token: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) node.data = { ...node.data, ai_message: node.data.ai_message + token }
  }

  function setCardStatus(cardId: string, status: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, status }
      scheduleSave()
    }
  }

  function updateCardData(cardId: string, data: Record<string, unknown>) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, ...data }
      scheduleSave()
    }
  }

  function updateCardField(cardId: string, field: 'user_message' | 'ai_message' | 'model_id', value: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, [field]: value }
      scheduleSave()
    }
  }

  function duplicateCard(cardId: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (!node) return
    const id = `card_${Date.now()}`
    nodes.value.push({
      id,
      type: 'card',
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: { ...node.data, status: 'done' },
    })
    scheduleSave()
  }

  function removeCard(cardId: string) {
    nodes.value = nodes.value.filter((n) => n.id !== cardId)
    edges.value = edges.value.filter((e) => e.source !== cardId && e.target !== cardId)
    persistCanvas()
  }

  function updateCanvasTitle(title: string) {
    if (!currentCanvas.value) return
    currentCanvas.value = { ...currentCanvas.value, title }
    persistCanvas()
  }

  function findExclusiveNodes(summarizedCardIds: string[]): string[] {
    const idSet = new Set(summarizedCardIds)
    const childrenMap = new Map<string, string[]>()
    for (const e of edges.value) {
      const list = childrenMap.get(e.source)
      if (list) list.push(e.target)
      else childrenMap.set(e.source, [e.target])
    }
    const exclusive: string[] = []
    for (let i = summarizedCardIds.length - 1; i >= 0; i--) {
      const cid = summarizedCardIds[i]
      const children = childrenMap.get(cid) ?? []
      const hasExternalChild = children.some((ch) => !idSet.has(ch))
      if (hasExternalChild) break
      exclusive.push(cid)
    }
    return exclusive
  }

  function insertSummaryNode(
    id: string,
    summarizedCardIds: string[],
    parentOfSummary: string | null,
  ) {
    if (parentOfSummary) {
      addEdge(parentOfSummary, id)
    }
    const lastSummarizedId = summarizedCardIds[summarizedCardIds.length - 1]
    const idSet = new Set(summarizedCardIds)
    for (const e of edges.value) {
      if (e.source === lastSummarizedId && !idSet.has(e.target) && e.target !== id) {
        e.source = id
      }
    }
    const exclusive = findExclusiveNodes(summarizedCardIds)
    suppressCards(exclusive)
  }

  function addSummaryCard(
    summaryText: string,
    summarizedCardIds: string[],
    parentOfSummary: string | null,
    position?: { x: number; y: number },
  ): string {
    const id = `card_${Date.now()}`
    const pos = position ?? { x: 200, y: 100 }
    nodes.value.push({
      id,
      type: 'card',
      position: pos,
      data: {
        user_message: '对话摘要',
        ai_message: summaryText,
        model_id: '',
        status: 'done',
        created_at: new Date().toISOString(),
        is_summary: true,
        summarized_card_ids: summarizedCardIds,
        is_suppressed: false,
      },
    })
    insertSummaryNode(id, summarizedCardIds, parentOfSummary)
    return id
  }

  function createSummaryPlaceholder(
    summarizedCardIds: string[],
    parentOfSummary: string | null,
    position?: { x: number; y: number },
  ): string {
    const id = `card_${Date.now()}`
    const pos = position ?? { x: 200, y: 100 }
    nodes.value.push({
      id,
      type: 'card',
      position: pos,
      data: {
        user_message: '对话摘要',
        ai_message: '',
        model_id: '',
        status: 'streaming',
        created_at: new Date().toISOString(),
        is_summary: true,
        summarized_card_ids: summarizedCardIds,
        is_suppressed: false,
      },
    })
    if (parentOfSummary) {
      addEdge(parentOfSummary, id)
    }
    scheduleSave()
    return id
  }

  function finalizeSummaryCard(cardId: string, summarizedCardIds: string[]) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, summarized_card_ids: summarizedCardIds }
    }
    const lastSummarizedId = summarizedCardIds[summarizedCardIds.length - 1]
    const idSet = new Set(summarizedCardIds)
    for (const e of edges.value) {
      if (e.source === lastSummarizedId && !idSet.has(e.target) && e.target !== cardId) {
        e.source = cardId
      }
    }
    const exclusive = findExclusiveNodes(summarizedCardIds)
    suppressCards(exclusive)
  }

  function finishSummaryCard(cardId: string, summaryText: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, ai_message: summaryText, status: 'done' }
      scheduleSave()
    }
  }

  function failSummaryCard(cardId: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, ai_message: '摘要生成失败', status: 'error' }
      scheduleSave()
    }
  }

  function suppressCards(cardIds: string[]) {
    for (const cardId of cardIds) {
      const node = nodes.value.find((n) => n.id === cardId)
      if (node) node.data = { ...node.data, is_suppressed: true }
    }
    scheduleSave()
  }

  function unsuppressCard(cardId: string) {
    const node = nodes.value.find((n) => n.id === cardId)
    if (node) {
      node.data = { ...node.data, is_suppressed: false }
      scheduleSave()
    }
  }

  return {
    currentCanvas,
    nodes,
    edges,
    saving,
    loadCanvas,
    persistCanvas,
    updateNodePosition,
    addEdge,
    removeEdge,
    addCard,
    updateCardAiMessage,
    setCardStatus,
    updateCardField,
    updateCardData,
    duplicateCard,
    removeCard,
    updateCanvasTitle,
    addSummaryCard,
    createSummaryPlaceholder,
    finishSummaryCard,
    finalizeSummaryCard,
    failSummaryCard,
    suppressCards,
    unsuppressCard,
  }
})
