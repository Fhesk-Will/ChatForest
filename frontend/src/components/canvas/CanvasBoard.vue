<template>
  <div class="canvas-wrapper">
    <CanvasToolbar @new-card="onNewCard" />

    <VueFlow
      v-model:nodes="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :default-edge-options="{ type: 'smoothstep', animated: false }"
      :delete-key-code="['Delete']"
      fit-view-on-init
      @connect="onConnect"
      @node-drag-stop="onDragStop"
      @edge-click="onEdgeClick"
      @node-context-menu="onNodeContextMenu"
    >
      <Background pattern-color="#d1cdc7" :gap="24" />
      <Controls />
      <MiniMap node-color="#e5e7eb" mask-color="rgba(248,249,250,0.7)" />
    </VueFlow>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <button class="context-menu-item" @click="contextMenuSummarize">
        <span class="ctx-icon">∑</span> 摘要到此处
      </button>
      <button class="context-menu-item" @click="contextMenuRetry">
        <span class="ctx-icon">↻</span> 重试
      </button>
      <button class="context-menu-item danger" @click="contextMenuDelete">
        <span class="ctx-icon">✕</span> 删除
      </button>
    </div>
    <div v-if="contextMenu.visible" class="context-menu-backdrop" @click="closeContextMenu" @contextmenu.prevent="closeContextMenu" />

    <!-- 根节点输入框（新建对话） -->
    <div v-if="showRootInput" class="send-panel" @click.self="showRootInput = false">
      <div class="send-box">
        <div class="send-title">新建对话</div>
        <select v-if="allModels.length" v-model="rootModel" class="send-model-select">
          <option v-for="m in allModels" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <textarea
          ref="rootInputRef"
          v-model="rootText"
          class="send-input"
          placeholder="输入消息... (Ctrl+Enter 发送)"
          @keydown.ctrl.enter="submitRoot"
          @keydown.meta.enter="submitRoot"
        />
        <div class="send-footer">
          <span class="send-hint">Ctrl+Enter 发送</span>
          <button class="send-btn" :disabled="!rootText.trim()" @click="submitRoot">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, markRaw, watch } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import type { Connection, NodeDragEvent, EdgeMouseEvent, NodeMouseEvent } from '@vue-flow/core'

import { marked } from 'marked'
import CardNode from './CardNode.vue'
import CanvasToolbar from './CanvasToolbar.vue'
import { useCanvasStore } from '../../stores/canvas'
import { useModelsStore } from '../../stores/models'
import { api } from '../../api'

marked.use({ breaks: true })

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const nodeTypes = { card: markRaw(CardNode) } as any

const store = useCanvasStore()
const modelsStore = useModelsStore()

const showRootInput = ref(false)
const rootText = ref('')
const rootModel = ref('')
const rootInputRef = ref<HTMLTextAreaElement | null>(null)
const contextMenu = ref<{ visible: boolean; x: number; y: number; nodeId: string }>({
  visible: false, x: 0, y: 0, nodeId: '',
})

const allModels = computed(() => {
  if (!modelsStore.config) return []
  return modelsStore.config.providers.flatMap((p) =>
    p.models.map((m) => ({ value: m, label: m }))
  )
})

watch(() => modelsStore.config, (cfg) => {
  if (cfg && !rootModel.value) rootModel.value = cfg.default_model.model
}, { immediate: true })

function onNewCard() {
  rootModel.value = modelsStore.config?.default_model.model ?? ''
  showRootInput.value = true
  rootText.value = ''
  nextTick(() => rootInputRef.value?.focus())
}

function onCardDuplicate(cardId: string) {
  store.duplicateCard(cardId)
}

function onCardRemove(cardId: string) {
  store.removeCard(cardId)
}

async function onCardRetry(cardId: string) {
  await retryMessage(cardId)
}

async function onCardSendInline(parentId: string, text: string, model: string) {
  await sendMessage(parentId, text, model)
}

// 注入 handlers 到所有节点
watch(
  () => store.nodes.length,
  () => {
    store.nodes.forEach((node) => {
      if (!node.data.onSendInline) {
        node.data = {
          ...node.data,
          onSendInline: onCardSendInline,
          onDuplicate: onCardDuplicate,
          onRemove: onCardRemove,
          onRetry: onCardRetry,
        }
      }
    })
  },
  { immediate: true },
)

function onConnect(connection: Connection) {
  if (connection.source && connection.target) {
    store.addEdge(connection.source, connection.target)
    // Auto-layout after reconnect
    nextTick(() => autoLayout())
  }
}

function onDragStop(event: NodeDragEvent) {
  store.updateNodePosition(event.node.id, event.node.position)
  // Auto-layout after drag
  nextTick(() => autoLayout())
}

function onEdgeClick(event: EdgeMouseEvent) {
  if (confirm('删除这条连线？')) {
    store.removeEdge(event.edge.id)
    nextTick(() => autoLayout())
  }
}

function onNodeContextMenu(event: NodeMouseEvent) {
  const mouseEvent = event.event as MouseEvent
  mouseEvent.preventDefault()
  contextMenu.value = {
    visible: true,
    x: mouseEvent.clientX,
    y: mouseEvent.clientY,
    nodeId: event.node.id,
  }
}

function closeContextMenu() {
  contextMenu.value = { ...contextMenu.value, visible: false }
}

async function contextMenuSummarize() {
  const nodeId = contextMenu.value.nodeId
  closeContextMenu()
  const canvasId = store.currentCanvas!.id

  // 先找位置和父节点
  const targetNode = store.nodes.find((n) => n.id === nodeId)
  const parentEdge = store.edges.find((e) => e.target === nodeId)
  const parentOfSummary = parentEdge?.source ?? null
  const position = targetNode?.position

  // 先创建占位节点
  const placeholderId = store.createSummaryPlaceholder([nodeId], parentOfSummary, position)
  nextTick(() => autoLayout())

  try {
    const result = await api.summarize({ canvas_id: canvasId, up_to_card_id: nodeId })
    store.finishSummaryCard(placeholderId, result.summary)
    store.finalizeSummaryCard(placeholderId, result.summarized_card_ids)
    nextTick(() => autoLayout())
  } catch (e) {
    console.error('摘要失败', e)
    store.failSummaryCard(placeholderId)
  }
}

function contextMenuRetry() {
  const nodeId = contextMenu.value.nodeId
  closeContextMenu()
  retryMessage(nodeId)
}

function contextMenuDelete() {
  const nodeId = contextMenu.value.nodeId
  closeContextMenu()
  if (confirm('确定删除该节点？')) {
    store.removeCard(nodeId)
    nextTick(() => autoLayout())
  }
}

/**
 * Auto-layout: Reingold-Tilford-style tree layout.
 * Each node's x is centered over its subtree; siblings are evenly spaced.
 */
function autoLayout() {
  const nodes = store.nodes
  const edges = store.edges
  if (nodes.length === 0) return

  const NODE_W = 360   // approximate card width + horizontal gap
  const V_GAP = 480    // vertical gap — must exceed max card height to prevent overlap
  const START_Y = 80

  // Build adjacency
  const childrenMap = new Map<string, string[]>()
  const parentMap = new Map<string, string>()
  for (const n of nodes) childrenMap.set(n.id, [])
  for (const e of edges) {
    childrenMap.get(e.source)?.push(e.target)
    parentMap.set(e.target, e.source)
  }

  // Find roots (no parent)
  const roots = nodes.filter((n) => !parentMap.has(n.id))
  if (roots.length === 0) return

  // Compute subtree leaf count (used to determine width allocation)
  const leafCount = new Map<string, number>()
  function countLeaves(id: string): number {
    const children = childrenMap.get(id) ?? []
    if (children.length === 0) { leafCount.set(id, 1); return 1 }
    const total = children.reduce((sum, cid) => sum + countLeaves(cid), 0)
    leafCount.set(id, total)
    return total
  }
  for (const r of roots) countLeaves(r.id)

  // Assign x positions by distributing leaf slots
  const xPos = new Map<string, number>()
  let globalLeafIndex = 0

  function assignX(id: string) {
    const children = childrenMap.get(id) ?? []
    if (children.length === 0) {
      xPos.set(id, globalLeafIndex * NODE_W)
      globalLeafIndex++
      return
    }
    for (const cid of children) assignX(cid)
    // Center parent over its children
    const firstChild = children[0]
    const lastChild = children[children.length - 1]
    const cx = ((xPos.get(firstChild) ?? 0) + (xPos.get(lastChild) ?? 0)) / 2
    xPos.set(id, cx)
  }

  // Layout each root tree side by side
  for (const r of roots) {
    assignX(r.id)
    globalLeafIndex++ // gap between separate root trees
  }

  // Assign y by BFS level
  const levelMap = new Map<string, number>()
  const queue: string[] = []
  for (const r of roots) { levelMap.set(r.id, 0); queue.push(r.id) }
  while (queue.length > 0) {
    const id = queue.shift()!
    const level = levelMap.get(id)!
    for (const cid of (childrenMap.get(id) ?? [])) {
      if (!levelMap.has(cid)) { levelMap.set(cid, level + 1); queue.push(cid) }
    }
  }

  // Apply positions
  for (const n of nodes) {
    const x = xPos.get(n.id) ?? 0
    const y = START_Y + (levelMap.get(n.id) ?? 0) * V_GAP
    n.position = { x, y }
    store.updateNodePosition(n.id, n.position)
  }
}

async function submitRoot() {
  const text = rootText.value.trim()
  if (!text) return
  showRootInput.value = false
  rootText.value = ''
  await sendMessage(null, text, rootModel.value)
}

async function sendMessage(parentId: string | null, text: string, model: string) {
  const provider_id = modelsStore.getProviderForModel(model)
  const canvasId = store.currentCanvas!.id

  let position: { x: number; y: number } | undefined
  if (parentId) {
    const parent = store.nodes.find((n) => n.id === parentId)
    if (parent) {
      const childCount = store.edges.filter((e) => e.source === parentId).length - 1
      position = { x: parent.position.x + childCount * 380, y: parent.position.y + (parent.data.cardHeight ?? 300) + 120 }
    }
  }

  const cardId = store.addCard(text, parentId, position, {
    model_id: model,
    onSendInline: onCardSendInline,
    onDuplicate: onCardDuplicate,
    onRemove: onCardRemove,
  })

  if (parentId) store.updateCardField(parentId, 'model_id', model)

  await api.chatStream(
    { canvas_id: canvasId, parent_card_id: parentId, user_message: text, provider_id, model },
    (token) => store.updateCardAiMessage(cardId, token),
    () => {
      store.setCardStatus(cardId, 'done')
      if (!parentId && store.currentCanvas?.title === '未命名画布') {
        summarizeTitle(cardId, text)
      }
      nextTick(() => autoLayout())
    },
    (err) => {
      store.updateCardAiMessage(cardId, `\n[错误: ${err}]`)
      store.setCardStatus(cardId, 'error')
    },
    (summary, summarizedCardIds) => {
      const firstId = summarizedCardIds[0]
      const parentEdge = store.edges.find((e) => e.target === firstId)
      const parentOfSummary = parentEdge?.source ?? null
      const firstNode = store.nodes.find((n) => n.id === firstId)
      store.addSummaryCard(summary, summarizedCardIds, parentOfSummary, firstNode?.position)
    },
  )
}

async function retryMessage(cardId: string, overrideModel?: string) {
  const node = store.nodes.find((n) => n.id === cardId)
  if (!node) return
  const canvasId = store.currentCanvas!.id
  const userMessage = node.data.user_message
  const model = overrideModel || node.data.model_id || modelsStore.config?.default_model.model || ''
  const provider_id = modelsStore.getProviderForModel(model)

  // 更新卡片的 model_id 为实际使用的模型
  store.updateCardData(cardId, { ai_message: '', status: 'streaming', model_id: model })

  // Find parent edge
  const parentEdge = store.edges.find((e) => e.target === cardId)
  const parentId = parentEdge?.source ?? null

  await api.chatStream(
    { canvas_id: canvasId, parent_card_id: parentId, user_message: userMessage, provider_id, model },
    (token) => store.updateCardAiMessage(cardId, token),
    () => {
      store.setCardStatus(cardId, 'done')
      nextTick(() => autoLayout())
    },
    (err) => {
      store.updateCardAiMessage(cardId, `\n[错误: ${err}]`)
      store.setCardStatus(cardId, 'error')
    },
    (summary, summarizedCardIds) => {
      const firstId = summarizedCardIds[0]
      const parentEdge = store.edges.find((e) => e.target === firstId)
      const parentOfSummary = parentEdge?.source ?? null
      const firstNode = store.nodes.find((n) => n.id === firstId)
      store.addSummaryCard(summary, summarizedCardIds, parentOfSummary, firstNode?.position)
    },
  )
}

async function summarizeTitle(cardId: string, userMessage: string) {
  const canvasId = store.currentCanvas!.id
  try {
    const result = await api.summarizeTitle(canvasId, userMessage)
    if (result.title) store.updateCanvasTitle(result.title)
  } catch { /* 静默失败 */ }
}

// Expose sendMessage and retryMessage for FocusMode / App
defineExpose({ sendMessage, retryMessage })
</script>

<style scoped>
.canvas-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f5f3f0;
}

.send-panel {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.send-box {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 16px;
  padding: 20px;
  width: 480px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.send-title { font-size: 14px; font-weight: 600; color: #1a1a1a; }

.send-model-select {
  background: #f5f3f0;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  color: #374151;
  font-size: 12px;
  padding: 5px 8px;
  font-family: inherit;
}
.send-model-select:focus { outline: none; border-color: #5b6e8a; }

.send-input {
  background: #f9f8f6;
  border: 1px solid #e0dcd5;
  border-radius: 10px;
  color: #1a1a1a;
  font-size: 14px;
  font-family: inherit;
  padding: 10px 12px;
  resize: vertical;
  min-height: 100px;
  width: 100%;
  box-sizing: border-box;
  line-height: 1.5;
}
.send-input:focus { outline: none; border-color: #5b6e8a; background: #fff; }
.send-input::-webkit-scrollbar { width: 3px; }
.send-input::-webkit-scrollbar-track { background: transparent; }
.send-input::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

.send-footer { display: flex; align-items: center; justify-content: space-between; }
.send-hint { font-size: 12px; color: #999; }

.send-btn {
  background: #5b6e8a; color: #ffffff; border: none;
  border-radius: 8px; padding: 7px 18px; font-size: 13px; font-weight: 600; cursor: pointer;
  font-family: inherit;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.send-btn:not(:disabled):hover { background: #4a5c6b; }

/* 右键菜单 */
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 199;
}
.context-menu {
  position: fixed;
  z-index: 200;
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  min-width: 140px;
}
.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
}
.context-menu-item:hover { background: #f5f3f0; }
.context-menu-item.danger:hover { background: #fef0f0; color: #ef4444; }
.ctx-icon { font-size: 14px; width: 18px; text-align: center; flex-shrink: 0; }
</style>

<style>
/* VueFlow overrides for warm theme */
.vue-flow__controls button:last-child { display: none !important; }
.vue-flow { background: #f5f3f0; }
.vue-flow__controls {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.vue-flow__controls button {
  background: #ffffff;
  border-bottom: 1px solid #e0dcd5;
  color: #5c5c5c;
}
.vue-flow__controls button:hover { background: #f5f3f0; }
.vue-flow__minimap {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 10px;
}
.vue-flow__edge-path { stroke: #c5bfb4 !important; stroke-width: 2.2 !important; }
</style>
