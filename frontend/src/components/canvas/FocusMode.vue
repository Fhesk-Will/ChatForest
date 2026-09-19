<template>
  <div class="focus-mode">
    <!-- 分支标签栏 -->
    <div class="branches-bar">
      <span class="branches-label">分支路径</span>
      <button
        v-for="(branch, idx) in branches"
        :key="branch.leafId"
        class="branch-tab"
        :class="{ active: branch.leafId === activeLeafId }"
        @click="switchBranch(branch.leafId)"
      >
        {{ branch.label }}
      </button>
      <span v-if="branches.length === 0" class="no-branches">暂无分支，请先在总览模式创建节点</span>
    </div>

    <!-- 对话内容 -->
    <div ref="chatContainer" class="chat-container">
      <template v-if="activePath.length > 0">
        <template v-for="node in activePath" :key="node.id">

          <!-- 用户消息 -->
          <div class="msg-group user-group">
            <div class="chat-message user">
              <div class="avatar user-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
              </div>
              <textarea
                v-if="editingNodes.has(node.id + '_user')"
                class="bubble user-bubble user-edit-textarea"
                :value="node.userMsg"
                @input="onUserEdit(node.id, $event)"
              />
              <div
                v-else
                class="bubble user-bubble"
              >{{ node.userMsg }}</div>
            </div>
            <div class="msg-toolbar user-toolbar">
              <button class="tool-btn" :title="editingNodes.has(node.id + '_user') ? '预览' : '编辑'" @click="toggleEdit(node.id + '_user')">
                <svg v-if="!editingNodes.has(node.id + '_user')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
              <button class="tool-btn" title="复制" @click="copyText(node.userMsg)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
              <button class="tool-btn" title="重试" @click="retryNode(node.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/></svg>
              </button>
              <button class="tool-btn danger" title="删除节点" @click="removeNode(node.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
              </button>
            </div>
          </div>

          <!-- AI 消息 -->
          <div v-if="node.aiMsg || node.status === 'streaming'" class="msg-group ai-group">
            <div class="chat-message ai">
              <div class="avatar ai-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M9 11V7a3 3 0 0 1 6 0v4"/><circle cx="9" cy="16" r="1" fill="currentColor"/><circle cx="15" cy="16" r="1" fill="currentColor"/></svg>
              </div>
              <div class="bubble ai-bubble">
                <textarea
                  v-if="editingNodes.has(node.id + '_ai')"
                  class="ai-edit-textarea"
                  :value="node.aiMsg"
                  @input="onAiEdit(node.id, $event)"
                />
                <div v-else class="ai-content markdown-body" v-html="renderMarkdown(node.aiMsg)" />
                <div v-if="node.status === 'streaming'" class="streaming-indicator">▌</div>
              </div>
            </div>
            <div class="msg-toolbar ai-toolbar">
              <select
                class="toolbar-model-select"
                :value="retryModelOverrides.get(node.id) ?? node.model"
                @change="onRetryModelChange(node.id, $event)"
                @mousedown.stop
              >
                <option v-for="m in allModels" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
              <button class="tool-btn" :title="editingNodes.has(node.id + '_ai') ? '预览' : '编辑'" @click="toggleEdit(node.id + '_ai')">
                <svg v-if="!editingNodes.has(node.id + '_ai')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
              <button class="tool-btn" title="复制" @click="copyText(node.aiMsg)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
              <button class="tool-btn" title="重试" @click="retryNode(node.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/></svg>
              </button>
              <button
                v-if="!isSummaryNode(node.id)"
                class="tool-btn"
                :class="{ 'summarizing': summarizingId === node.id }"
                title="摘要到此处"
                :disabled="!!summarizingId"
                @click="summarizeUpTo(node.id)"
              >
                <svg v-if="summarizingId !== node.id" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 6h16M4 10h10M4 14h6"/>
                </svg>
                <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" opacity="0.3"/>
                  <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                </svg>
              </button>
              <button class="tool-btn danger" title="删除节点" @click="removeNode(node.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
              </button>
            </div>
          </div>

        </template>
      </template>
      <div v-else class="empty-hint">暂无对话，请先在总览模式创建节点</div>
    </div>

    <!-- 输入框 -->
    <div class="input-area">
      <div class="input-box">
        <select v-if="allModels.length" v-model="inputModel" class="model-select">
          <option v-for="m in allModels" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <textarea
          v-model="inputText"
          class="input-textarea"
          placeholder="输入消息，在当前分支末端添加新对话... (Ctrl+Enter 发送)"
          rows="2"
          @keydown.ctrl.enter.prevent="handleSend"
          @keydown.meta.enter.prevent="handleSend"
        />
        <button class="send-btn" :disabled="!inputText.trim()" @click="handleSend">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useCanvasStore } from '../../stores/canvas'
import { useModelsStore } from '../../stores/models'
import { api } from '../../api'

marked.use({ gfm: true, breaks: true })

const emit = defineEmits<{
  send: [parentId: string | null, text: string, model: string]
  removeNode: [nodeId: string]
  retryNode: [nodeId: string, userMsg: string, model: string]
}>()

const store = useCanvasStore()
const modelsStore = useModelsStore()

const chatContainer = ref<HTMLElement | null>(null)
const inputText = ref('')
const inputModel = ref('')
const activeLeafId = ref<string | null>(null)
const branchScrollPositions = new Map<string, number>()
const editingNodes = reactive(new Set<string>())
const summarizingId = ref<string | null>(null)
const retryModelOverrides = reactive(new Map<string, string>())

const allModels = computed(() => {
  if (!modelsStore.config) return []
  return modelsStore.config.providers.flatMap((p) =>
    p.models.map((m) => ({ value: m, label: m }))
  )
})

watch(() => modelsStore.config, (cfg) => {
  if (cfg && !inputModel.value) inputModel.value = cfg.default_model.model
}, { immediate: true })

interface TreeNode {
  id: string
  userMsg: string
  aiMsg: string
  status: string
  parentId: string | null
  childrenIds: string[]
  model: string
}

const treeNodes = computed((): Map<string, TreeNode> => {
  const map = new Map<string, TreeNode>()
  for (const n of store.nodes) {
    map.set(n.id, {
      id: n.id,
      userMsg: n.data.user_message,
      aiMsg: n.data.ai_message,
      status: n.data.status,
      parentId: null,
      childrenIds: [],
      model: n.data.model_id || modelsStore.config?.default_model.model || '',
    })
  }
  for (const e of store.edges) {
    const parent = map.get(e.source)
    const child = map.get(e.target)
    if (parent && child) {
      parent.childrenIds.push(e.target)
      child.parentId = e.source
    }
  }
  return map
})

function getLeafNodes(): TreeNode[] {
  const leaves: TreeNode[] = []
  treeNodes.value.forEach((n) => {
    if (n.childrenIds.length === 0) leaves.push(n)
  })
  // Sort by canvas x position so branch tab order matches left-to-right tree layout
  leaves.sort((a, b) => {
    const nodeA = store.nodes.find((n) => n.id === a.id)
    const nodeB = store.nodes.find((n) => n.id === b.id)
    return (nodeA?.position.x ?? 0) - (nodeB?.position.x ?? 0)
  })
  return leaves
}

function getPathToRoot(nodeId: string): TreeNode[] {
  const path: TreeNode[] = []
  let cur = treeNodes.value.get(nodeId)
  while (cur) {
    path.unshift(cur)
    cur = cur.parentId ? treeNodes.value.get(cur.parentId) : undefined
  }
  return path
}

function getBranchLabel(path: TreeNode[], idx: number): string {
  for (const node of path) {
    if (node.parentId) {
      const parent = treeNodes.value.get(node.parentId)
      if (parent && parent.childrenIds.length > 1) {
        const text = node.userMsg.trim()
        return `分支${idx + 1}: ${text.substring(0, 18)}${text.length > 18 ? '…' : ''}`
      }
    }
  }
  const leaf = path[path.length - 1]
  const text = leaf?.userMsg.trim() ?? ''
  return `分支${idx + 1}: ${text.substring(0, 18)}${text.length > 18 ? '…' : ''}`
}

const branches = computed(() => {
  const leaves = getLeafNodes()
  return leaves
    .filter((leaf) => {
      const node = store.nodes.find((n) => n.id === leaf.id)
      return !node?.data.is_suppressed
    })
    .map((leaf, idx) => {
      const path = getPathToRoot(leaf.id)
      return { leafId: leaf.id, label: getBranchLabel(path, idx), path }
    })
})

const activePath = computed(() => {
  if (!activeLeafId.value) return []
  const branch = branches.value.find((b) => b.leafId === activeLeafId.value)
  if (!branch) return []
  // 过滤掉 suppressed 节点（已被摘要覆盖）
  return branch.path.filter((n) => {
    const node = store.nodes.find((s) => s.id === n.id)
    return !node?.data.is_suppressed
  })
})

watch(branches, (bs) => {
  if (!activeLeafId.value || !bs.find((b) => b.leafId === activeLeafId.value)) {
    activeLeafId.value = bs[0]?.leafId ?? null
  }
}, { immediate: true })

let prevPathLength = 0
let isNewMessage = false
watch(activePath, (path) => {
  const newLength = path.length
  if (newLength > prevPathLength) {
    isNewMessage = true
    nextTick(() => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
      isNewMessage = false
    })
  }
  prevPathLength = newLength
})

function switchBranch(leafId: string) {
  if (activeLeafId.value === leafId) return
  if (activeLeafId.value && chatContainer.value) {
    branchScrollPositions.set(activeLeafId.value, chatContainer.value.scrollTop)
  }
  activeLeafId.value = leafId
  nextTick(() => {
    if (chatContainer.value) {
      const saved = branchScrollPositions.get(leafId)
      if (saved !== undefined) {
        chatContainer.value.scrollTop = saved
      } else {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }
  })
}

function toggleEdit(key: string) {
  if (editingNodes.has(key)) {
    editingNodes.delete(key)
  } else {
    editingNodes.add(key)
  }
}

function normalizeMarkdown(text: string): string {
  // Insert blank line before block-level markers that need one to be recognized
  return text
    .replace(/([^\n])\n(#{1,6} )/g, '$1\n\n$2')       // before headings
    .replace(/([^\n])\n(> )/g, '$1\n\n$2')              // before blockquotes
    .replace(/([^|\n])\n(\|)/g, '$1\n\n$2')             // before first table row only (not between rows)
    .replace(/([^\n])\n([-*+] |\d+\. )/g, '$1\n\n$2')  // before list items
    .replace(/([^\n])\n(```)/g, '$1\n\n$2')             // before code fences
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    return DOMPurify.sanitize(marked.parse(normalizeMarkdown(text)) as string)
  } catch {
    return text
  }
}

function onUserEdit(nodeId: string, event: Event) {
  const el = event.target as HTMLTextAreaElement
  store.updateCardField(nodeId, 'user_message', el.value)
}

function onAiEdit(nodeId: string, event: Event) {
  const el = event.target as HTMLTextAreaElement
  store.updateCardField(nodeId, 'ai_message', el.value)
}

function copyText(text: string) {
  navigator.clipboard.writeText(text)
}

function removeNode(nodeId: string) {
  if (confirm('确定删除该节点吗？这将删除整个对话轮次。')) {
    emit('removeNode', nodeId)
  }
}

function retryNode(nodeId: string) {
  const node = treeNodes.value.get(nodeId)
  if (!node) return
  const model = retryModelOverrides.get(nodeId) ?? node.model
  retryModelOverrides.delete(nodeId)
  emit('retryNode', nodeId, node.userMsg, model)
}

function onRetryModelChange(nodeId: string, event: Event) {
  const value = (event.target as HTMLSelectElement).value
  retryModelOverrides.set(nodeId, value)
}

function isSummaryNode(nodeId: string): boolean {
  const node = store.nodes.find((n) => n.id === nodeId)
  return !!node?.data.is_summary
}

async function summarizeUpTo(cardId: string) {
  if (summarizingId.value) return
  summarizingId.value = cardId
  const canvasId = store.currentCanvas?.id
  if (!canvasId) { summarizingId.value = null; return }

  const firstNode = store.nodes.find((n) => n.id === cardId)
  const parentEdge = store.edges.find((e) => e.target === cardId)
  const parentOfSummary = parentEdge?.source ?? null
  const position = firstNode ? { x: firstNode.position.x, y: firstNode.position.y } : undefined

  const placeholderId = store.createSummaryPlaceholder([cardId], parentOfSummary, position)
  activeLeafId.value = placeholderId

  try {
    const result = await api.summarize({ canvas_id: canvasId, up_to_card_id: cardId })

    store.finishSummaryCard(placeholderId, result.summary)
    store.finalizeSummaryCard(placeholderId, result.summarized_card_ids)
  } catch (e) {
    console.error('摘要失败', e)
    store.failSummaryCard(placeholderId)
  } finally {
    summarizingId.value = null
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  const parentId = activeLeafId.value
  emit('send', parentId, text, inputModel.value)
  inputText.value = ''
}

function setActiveLeaf(leafId: string) {
  activeLeafId.value = leafId
}

defineExpose({ setActiveLeaf })
</script>

<style scoped>
.focus-mode {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #faf9f7;
}

.branches-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #ffffff;
  border-bottom: 1px solid #e0dcd5;
  overflow-x: auto;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  z-index: 10;
}
.branches-bar::-webkit-scrollbar { height: 3px; }
.branches-bar::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

.branches-label {
  font-size: 11px;
  font-weight: 700;
  color: #999;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
  margin-right: 4px;
  flex-shrink: 0;
}

.branch-tab {
  padding: 5px 14px;
  border-radius: 20px;
  border: 1.5px solid #e0dcd5;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  color: #5c5c5c;
  transition: all 0.15s;
  font-family: inherit;
  flex-shrink: 0;
}
.branch-tab:hover { border-color: #8a9db5; color: #1a1a1a; }
.branch-tab.active {
  background: #5b6e8a;
  color: #fff;
  border-color: #5b6e8a;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(91,110,138,0.25);
}

.no-branches { font-size: 12px; color: #999; }

/* Chat container — 100px side padding */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 100px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.chat-container::-webkit-scrollbar { width: 4px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

/* msg-group wraps the bubble row + toolbar row */
.msg-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

/* Message row: bubble + avatar */
.chat-message {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
}
.chat-message.user {
  /* avatar is first in DOM, bubble is second — row-reverse puts avatar on right */
  flex-direction: row-reverse;
}
.chat-message.ai {
  flex-direction: row;
}

/* Avatars */
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  align-self: flex-start;
  margin-top: 2px;
}
.avatar svg { width: 18px; height: 18px; }
.user-avatar { background: #d6e0f0; color: #3a5a8a; }
.ai-avatar { background: #e0ecce; color: #4a7a2a; }

/* Bubbles */
.bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

/* User bubble: 80% of available width (container - avatar - gap) */
.user-bubble {
  background: #e8f0fe;
  color: #1a3a5c;
  border-bottom-right-radius: 4px;
  width: calc(80% - 40px);
  min-height: 38px;
  white-space: pre-wrap;
}

/* User bubble in edit mode — textarea shares same visual style */
.user-edit-textarea {
  border: none;
  outline: 2px solid #8a9db5;
  outline-offset: 2px;
  resize: vertical;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.7;
  cursor: text;
  min-height: 60px;
}

/* AI bubble: full available width */
.ai-bubble {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  color: #1a1a1a;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  width: calc(100% - 40px);
}

.ai-content { min-height: 20px; }

.ai-edit-textarea {
  width: 100%;
  min-height: 120px;
  background: #f9f8f6;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  color: #1a1a1a;
  font-size: 13px;
  font-family: inherit;
  padding: 6px 8px;
  resize: vertical;
  line-height: 1.6;
  outline: none;
  box-sizing: border-box;
}
.ai-edit-textarea:focus { border-color: #5b6e8a; }

.streaming-indicator {
  color: #5b6e8a;
  animation: blink 0.8s infinite;
  font-size: 14px;
  line-height: 1;
  margin-top: 4px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* Toolbar row — sits below the bubble, aligned to the bubble side */
.msg-toolbar {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
  padding: 0 40px; /* indent past avatar width+gap */
}
.msg-group:hover .msg-toolbar { opacity: 1; }

.user-toolbar {
  justify-content: flex-end;
}
.ai-toolbar {
  justify-content: flex-start;
}

.tool-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 3px 5px;
  border-radius: 5px;
  transition: background 0.15s;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tool-btn svg { width: 13px; height: 13px; stroke: #9ca3af; }
.tool-btn:hover { background: #f0ede8; }
.tool-btn:hover svg { stroke: #374151; }
.tool-btn.danger:hover { background: #fef0f0; }
.tool-btn.danger:hover svg { stroke: #ef4444; }
.tool-btn.summarizing svg { stroke: #f59e0b; animation: pulse 1s infinite; }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.toolbar-model-select {
  background: #f5f3f0;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  color: #5c5c5c;
  font-size: 11px;
  padding: 2px 6px;
  cursor: pointer;
  font-family: inherit;
  max-width: 120px;
}
.toolbar-model-select:focus { outline: none; border-color: #5b6e8a; }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.tool-btn .spin { animation: spin 1s linear infinite; }

.empty-hint {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 60px 0;
}

/* Input area */
.input-area {
  flex-shrink: 0;
  padding: 10px 100px 16px;
  background: #faf9f7;
  border-top: 1px solid #e0dcd5;
}

.input-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  border: 1.5px solid #e0dcd5;
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: border-color 0.15s;
}
.input-box:focus-within { border-color: #8a9db5; }

.model-select {
  background: #f5f3f0;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  color: #374151;
  font-size: 11px;
  padding: 3px 7px;
  align-self: flex-start;
  cursor: pointer;
  font-family: inherit;
}
.model-select:focus { outline: none; border-color: #5b6e8a; }

.input-textarea {
  background: transparent;
  border: none;
  color: #1a1a1a;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  width: 100%;
  line-height: 1.6;
  outline: none;
}
.input-textarea::placeholder { color: #bbb; }
.input-textarea::-webkit-scrollbar { width: 3px; }
.input-textarea::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

.send-btn {
  align-self: flex-end;
  background: #5b6e8a;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.send-btn:not(:disabled):hover { background: #4a5c6b; }
</style>

<style>
.focus-mode .markdown-body p { margin: 0 0 8px; line-height: 1.7; }
.focus-mode .markdown-body p:last-child { margin-bottom: 0; }
.focus-mode .markdown-body h1 { font-size: 18px; font-weight: 700; margin: 12px 0 6px; }
.focus-mode .markdown-body h2 { font-size: 16px; font-weight: 700; margin: 10px 0 5px; }
.focus-mode .markdown-body h3 { font-size: 14px; font-weight: 600; margin: 8px 0 4px; }
.focus-mode .markdown-body pre {
  background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 8px 10px; overflow-x: auto; font-size: 12px; margin: 6px 0;
}
.focus-mode .markdown-body code { font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; }
.focus-mode .markdown-body pre code { background: none; padding: 0; }
.focus-mode .markdown-body code:not(pre code) { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }
.focus-mode .markdown-body ul, .focus-mode .markdown-body ol { padding-left: 20px; margin: 4px 0 8px; }
.focus-mode .markdown-body li { margin: 3px 0; line-height: 1.6; }
.focus-mode .markdown-body strong { font-weight: 700; }
.focus-mode .markdown-body blockquote { border-left: 3px solid #d1d5db; margin: 6px 0; padding: 2px 0 2px 10px; color: #6b7280; }
.focus-mode .markdown-body table { border-collapse: collapse; width: 100%; font-size: 12px; margin: 6px 0; }
.focus-mode .markdown-body th, .focus-mode .markdown-body td { border: 1px solid #e5e7eb; padding: 4px 8px; }
.focus-mode .markdown-body th { background: #f9fafb; font-weight: 600; }
.focus-mode .markdown-body a { color: #5b6e8a; text-decoration: underline; }
</style>
