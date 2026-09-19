<template>
  <div
    class="card-node"
    :class="[data.status, { selected, 'is-summary': data.is_summary, 'is-suppressed': data.is_suppressed }]"
    :style="{ width: cardWidth + 'px' }"
  >
    <Handle type="target" :position="Position.Top" />

    <!-- 四边/四角 resize handles（在卡片内侧，不超出边界） -->
    <div class="rh rh-top"    @mousedown.stop="startResize('top', $event)" />
    <div class="rh rh-bottom" @mousedown.stop="startResize('bottom', $event)" />
    <div class="rh rh-left"   @mousedown.stop="startResize('left', $event)" />
    <div class="rh rh-right"  @mousedown.stop="startResize('right', $event)" />
    <div class="rh rh-tl"     @mousedown.stop="startResize('tl', $event)" />
    <div class="rh rh-tr"     @mousedown.stop="startResize('tr', $event)" />
    <div class="rh rh-bl"     @mousedown.stop="startResize('bl', $event)" />
    <div class="rh rh-br"     @mousedown.stop="startResize('br', $event)" />

    <!-- 头部（拖动区域） -->
    <div class="card-header">
      <span v-if="data.is_summary" class="summary-icon" title="摘要节点">∑</span>
      <span v-else class="status-dot" :title="data.status" />
      <span class="card-time">{{ formatTime(data.created_at) }}</span>
      <select
        v-if="allModels.length"
        class="model-select"
        :value="data.model_id || defaultModel"
        @change="onModelChange"
        @mousedown.stop
        @wheel.stop
      >
        <option v-for="m in allModels" :key="m.value" :value="m.value">{{ m.label }}</option>
      </select>
      <div class="card-actions">
        <button title="重试" @mousedown.stop @click.stop="data.onRetry?.(id)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/></svg>
        </button>
        <button title="复制卡片" @mousedown.stop @click.stop="data.onDuplicate?.(id)">⧉</button>
        <button title="删除卡片" @mousedown.stop @click.stop="data.onRemove?.(id)">✕</button>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="card-body" :style="{ height: cardHeight + 'px' }">
      <!-- 用户消息 -->
      <div class="msg-section" :style="{ height: userHeight + 'px' }">
        <div class="msg-label user-label">User</div>
        <textarea
          class="msg-textarea"
          :value="data.user_message"
          placeholder="用户消息..."
          @input="onEdit('user_message', $event)"
          @mousedown.stop
          @wheel.stop
        />
      </div>

      <!-- 分隔拖拽条 -->
      <div class="divider" @mousedown.stop="startDividerDrag">
        <div class="divider-line" />
      </div>

      <!-- AI 回答 -->
      <div class="msg-section ai-section">
        <div class="msg-label ai-label">
          AI
          <button
            v-if="data.status === 'done' || data.status === 'error'"
            class="edit-toggle"
            :title="editingAi ? '预览' : '编辑'"
            @mousedown.stop
            @click.stop="editingAi = !editingAi"
          >{{ editingAi ? '预览' : '编辑' }}</button>
        </div>
        <textarea
          v-if="editingAi || data.status === 'streaming' || data.status === 'idle'"
          class="msg-textarea"
          :value="data.ai_message"
          placeholder="AI 回答将在此显示..."
          :readonly="data.status === 'streaming'"
          @input="onEdit('ai_message', $event)"
          @mousedown.stop
          @wheel.stop
        />
        <div
          v-else
          class="msg-textarea markdown-body"
          v-html="renderedAi"
          @wheel.stop
        />
        <div v-if="data.status === 'streaming'" class="streaming-indicator">▌</div>
      </div>
    </div>

    <Handle type="source" :position="Position.Bottom" />

    <!-- 选中时底部输入框 -->
    <Transition name="input-fade">
      <div v-if="selected && data.status !== 'streaming'" class="inline-input" @mousedown.stop>
        <select
          v-if="allModels.length"
          class="inline-model-select"
          v-model="inlineModel"
          @mousedown.stop
          @wheel.stop
        >
          <option v-for="m in allModels" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <textarea
          ref="inlineInputRef"
          v-model="inlineText"
          class="inline-textarea"
          placeholder="继续对话... (Ctrl+Enter 发送)"
          rows="2"
          @keydown.ctrl.enter.prevent="submitInline"
          @keydown.meta.enter.prevent="submitInline"
          @mousedown.stop
          @wheel.stop
        />
        <button class="inline-send-btn" :disabled="!inlineText.trim()" @mousedown.stop @click.stop="submitInline">发送</button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Handle, Position, useVueFlow } from '@vue-flow/core'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useCanvasStore } from '../../stores/canvas'
import { useModelsStore } from '../../stores/models'

marked.use({ gfm: true, breaks: true })

const props = defineProps<{
  id: string
  selected?: boolean
  data: {
    user_message: string
    ai_message: string
    model_id: string
    status: string
    created_at: string
    is_summary?: boolean
    summarized_card_ids?: string[]
    is_suppressed?: boolean
    cardWidth?: number
    cardHeight?: number
    userRatio?: number
    onDuplicate?: (id: string) => void
    onRemove?: (id: string) => void
    onRetry?: (id: string) => void
    onSendInline?: (id: string, text: string, model: string) => void
  }
}>()

const store = useCanvasStore()
const modelsStore = useModelsStore()
const { updateNode } = useVueFlow()

const DIVIDER_H = 8
const MIN_SECTION_H = 50

const editingAi = ref(false)
const cardWidth = ref(props.data.cardWidth ?? 340)
const cardHeight = ref(props.data.cardHeight ?? 300)
const userRatio = ref(props.data.userRatio ?? 0.38)
const inlineText = ref('')
const inlineInputRef = ref<HTMLTextAreaElement | null>(null)

// user 区域像素高度（label 20px + textarea）
const userHeight = computed(() =>
  Math.max(MIN_SECTION_H, Math.round((cardHeight.value - DIVIDER_H) * userRatio.value))
)

const allModels = computed(() => {
  if (!modelsStore.config) return []
  return modelsStore.config.providers.flatMap((p) =>
    p.models.map((m) => ({ value: m, label: m }))
  )
})
const defaultModel = computed(() => modelsStore.config?.default_model.model ?? '')
const inlineModel = ref(props.data.model_id || defaultModel.value)
watch(() => props.data.model_id, (v) => { if (v) inlineModel.value = v })
watch(defaultModel, (v) => { if (!props.data.model_id) inlineModel.value = v })

watch(() => props.selected, (v) => {
  if (v) nextTick(() => inlineInputRef.value?.focus())
})

function normalizeMarkdown(text: string): string {
  return text
    .replace(/([^\n])\n(#{1,6} )/g, '$1\n\n$2')
    .replace(/([^\n])\n(> )/g, '$1\n\n$2')
    .replace(/([^|\n])\n(\|)/g, '$1\n\n$2')
    .replace(/([^\n])\n([-*+] |\d+\. )/g, '$1\n\n$2')
    .replace(/([^\n])\n(```)/g, '$1\n\n$2')
}

const renderedAi = computed(() => {
  if (!props.data.ai_message) return ''
  try {
    const html = marked.parse(normalizeMarkdown(props.data.ai_message)) as string
    return DOMPurify.sanitize(html)
  } catch {
    return props.data.ai_message
  }
})

function onEdit(field: 'user_message' | 'ai_message', event: Event) {
  store.updateCardField(props.id, field, (event.target as HTMLTextAreaElement).value)
}

function onModelChange(event: Event) {
  store.updateCardField(props.id, 'model_id' as any, (event.target as HTMLSelectElement).value)
}

function submitInline() {
  const text = inlineText.value.trim()
  if (!text) return
  inlineText.value = ''
  props.data.onSendInline?.(props.id, text, inlineModel.value)
}

function formatTime(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function saveSize() {
  store.updateCardData(props.id, {
    cardWidth: cardWidth.value,
    cardHeight: cardHeight.value,
    userRatio: userRatio.value,
  })
}

function startDividerDrag(e: MouseEvent) {
  e.preventDefault()
  const startY = e.clientY
  const startUserH = userHeight.value
  const totalH = cardHeight.value

  function onMove(ev: MouseEvent) {
    const delta = ev.clientY - startY
    const newUserH = Math.max(MIN_SECTION_H, Math.min(totalH - DIVIDER_H - MIN_SECTION_H, startUserH + delta))
    userRatio.value = newUserH / (totalH - DIVIDER_H)
  }
  function onUp() {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    saveSize()
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function startResize(dir: string, e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startY = e.clientY
  const startW = cardWidth.value
  const startH = cardHeight.value
  const node = store.nodes.find((n) => n.id === props.id)
  const startPosX = node?.position.x ?? 0
  const startPosY = node?.position.y ?? 0

  function onMove(ev: MouseEvent) {
    const dx = ev.clientX - startX
    const dy = ev.clientY - startY

    if (dir === 'right' || dir === 'tr' || dir === 'br') {
      cardWidth.value = Math.max(280, Math.min(900, startW + dx))
    }
    if (dir === 'left' || dir === 'tl' || dir === 'bl') {
      const newW = Math.max(280, Math.min(900, startW - dx))
      cardWidth.value = newW
      updateNode(props.id, { position: { x: startPosX + (startW - newW), y: startPosY } })
    }
    if (dir === 'bottom' || dir === 'bl' || dir === 'br') {
      cardHeight.value = Math.max(150, Math.min(1200, startH + dy))
    }
    if (dir === 'top' || dir === 'tl' || dir === 'tr') {
      const newH = Math.max(150, Math.min(1200, startH - dy))
      cardHeight.value = newH
      updateNode(props.id, { position: { x: startPosX, y: startPosY + (startH - newH) } })
    }
  }
  function onUp() {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    saveSize()
    const n = store.nodes.find((n) => n.id === props.id)
    if (n) store.updateNodePosition(props.id, n.position)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.card-node {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 14px;
  min-width: 280px;
  font-size: 13px;
  color: #1a1a1a;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
}
.card-node.streaming { border-color: #5b6e8a; box-shadow: 0 2px 8px rgba(91,110,138,0.18); }
.card-node.error { border-color: #ef4444; }
.card-node.selected { border-color: #5b6e8a; box-shadow: 0 0 0 3px rgba(91,110,138,0.15), 0 2px 8px rgba(0,0,0,0.08); }

.card-node.is-summary { background: #fffbeb; border-color: #f59e0b; }
.card-node.is-summary .card-header { background: #fef3c7; border-bottom-color: #fde68a; }
.card-node.is-suppressed { opacity: 0.45; filter: grayscale(0.4); }
.card-node.is-suppressed:hover { opacity: 0.7; }

/* Resize handles — 在卡片内侧边缘，不超出边界 */
.rh { position: absolute; z-index: 20; }
.rh-top    { top: 0;    left: 12px; right: 12px; height: 6px; cursor: ns-resize; border-radius: 12px 12px 0 0; }
.rh-bottom { bottom: 0; left: 12px; right: 12px; height: 6px; cursor: ns-resize; }
.rh-left   { left: 0;   top: 12px;  bottom: 12px; width: 6px; cursor: ew-resize; border-radius: 12px 0 0 12px; }
.rh-right  { right: 0;  top: 12px;  bottom: 12px; width: 6px; cursor: ew-resize; }
.rh-tl { top: 0; left: 0;   width: 14px; height: 14px; cursor: nwse-resize; border-radius: 12px 0 0 0; }
.rh-tr { top: 0; right: 0;  width: 14px; height: 14px; cursor: nesw-resize; border-radius: 0 12px 0 0; }
.rh-bl { bottom: 0; left: 0;  width: 14px; height: 14px; cursor: nesw-resize; border-radius: 0 0 0 12px; }
.rh-br { bottom: 0; right: 0; width: 14px; height: 14px; cursor: nwse-resize; border-radius: 0 0 12px 0; }

/* 头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px 7px;
  border-bottom: 1px solid #ebe7e1;
  flex-shrink: 0;
  cursor: grab;
  border-radius: 14px 14px 0 0;
  background: #faf9f7;
}
.card-header:active { cursor: grabbing; }

.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #7aab5a;
  flex-shrink: 0;
}
.streaming .status-dot { background: #5b6e8a; animation: pulse 1s infinite; }
.error .status-dot { background: #ef4444; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

.summary-icon {
  font-size: 13px;
  font-weight: 700;
  color: #d97706;
  flex-shrink: 0;
  line-height: 1;
}

.card-time { font-size: 11px; color: #bbb; }

.model-select {
  flex: 1;
  background: #f0ede8;
  border: 1px solid #e0dcd5;
  border-radius: 10px;
  color: #5c5c5c;
  font-size: 11px;
  padding: 2px 6px;
  cursor: pointer;
  min-width: 0;
  font-family: inherit;
}
.model-select:focus { outline: none; border-color: #5b6e8a; }

.card-actions { display: flex; gap: 2px; flex-shrink: 0; }
.card-actions button {
  background: none; border: none; color: #bbb;
  cursor: pointer; padding: 2px 6px; border-radius: 5px; font-size: 13px;
}
.card-actions button:hover { background: #f0ede8; color: #5c5c5c; }

/* 内容区 */
.card-body {
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  gap: 0;
  flex-shrink: 0;
  overflow: visible;
}

.msg-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-section {
  flex: 1;
  min-height: 50px;
}

.msg-label {
  font-size: 10px; font-weight: 700; color: #bbb;
  text-transform: uppercase; letter-spacing: 0.6px;
  display: flex; align-items: center; gap: 6px;
  flex-shrink: 0;
  padding: 0 0 3px;
  height: 20px;
}
.user-label { color: #7a9cc6; }
.ai-label { color: #9ab87a; }

.edit-toggle {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  font-size: 10px;
  padding: 1px 6px;
  color: #6b7280;
  font-weight: 500;
}
.edit-toggle:hover { background: #e5e7eb; color: #374151; }

.msg-textarea {
  flex: 1;
  background: #f9f8f6;
  border: 1px solid #e0dcd5;
  border-radius: 7px;
  color: #1a1a1a;
  font-size: 13px;
  font-family: inherit;
  padding: 7px 9px;
  resize: none;
  width: 100%;
  box-sizing: border-box;
  line-height: 1.6;
  overflow-y: auto;
}
.msg-textarea:focus { outline: none; border-color: #5b6e8a; background: #fff; }
.msg-textarea::-webkit-scrollbar { width: 3px; }
.msg-textarea::-webkit-scrollbar-track { background: transparent; }
.msg-textarea::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

/* 分隔拖拽条 */
.divider {
  height: 8px;
  flex-shrink: 0;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
}
.divider-line {
  width: 36px;
  height: 3px;
  background: #e5e7eb;
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}
.card-node:hover .divider-line { opacity: 1; }

/* Markdown 渲染区 */
.markdown-body {
  overflow-y: auto;
  cursor: text;
  white-space: normal;
}
.markdown-body::-webkit-scrollbar { width: 3px; }
.markdown-body::-webkit-scrollbar-track { background: transparent; }
.markdown-body::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

.streaming-indicator {
  color: #3b82f6; animation: blink 0.8s infinite; font-size: 16px; line-height: 1; flex-shrink: 0;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* 底部内联输入框 */
.inline-input {
  border-top: 1px solid #ebe7e1;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  background: #faf9f7;
  border-radius: 0 0 14px 14px;
}

.inline-model-select {
  background: #f0ede8;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  color: #5c5c5c;
  font-size: 11px;
  padding: 3px 6px;
  width: 100%;
  font-family: inherit;
}
.inline-model-select:focus { outline: none; border-color: #5b6e8a; }

.inline-textarea {
  background: #ffffff;
  border: 1px solid #e0dcd5;
  border-radius: 7px;
  color: #1a1a1a;
  font-size: 13px;
  font-family: inherit;
  padding: 7px 9px;
  resize: none;
  width: 100%;
  box-sizing: border-box;
  line-height: 1.5;
}
.inline-textarea:focus { outline: none; border-color: #5b6e8a; }
.inline-textarea::-webkit-scrollbar { width: 3px; }
.inline-textarea::-webkit-scrollbar-track { background: transparent; }
.inline-textarea::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

.inline-send-btn {
  align-self: flex-end;
  background: #5b6e8a; color: #ffffff; border: none;
  border-radius: 8px; padding: 6px 16px; font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: inherit;
}
.inline-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.inline-send-btn:not(:disabled):hover { background: #4a5c6b; }

.input-fade-enter-active, .input-fade-leave-active { transition: opacity 0.15s, transform 0.15s; }
.input-fade-enter-from, .input-fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>

<style>
/* Markdown 内容样式（全局，确保 v-html 渲染的内容能被命中） */
.markdown-body p { margin: 0 0 8px; line-height: 1.6; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body h1 { font-size: 18px; font-weight: 700; margin: 12px 0 6px; color: #111827; }
.markdown-body h2 { font-size: 16px; font-weight: 700; margin: 10px 0 5px; color: #111827; }
.markdown-body h3 { font-size: 14px; font-weight: 600; margin: 8px 0 4px; color: #111827; }
.markdown-body h4, .markdown-body h5, .markdown-body h6 { font-size: 13px; font-weight: 600; margin: 6px 0 3px; }
.markdown-body pre {
  background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 8px 10px; overflow-x: auto; font-size: 12px; margin: 6px 0; line-height: 1.5;
}
.markdown-body code { font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; }
.markdown-body pre code { background: none; padding: 0; color: inherit; }
.markdown-body code:not(pre code) { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; color: #374151; }
.markdown-body ul, .markdown-body ol { padding-left: 20px; margin: 4px 0 8px; }
.markdown-body li { margin: 3px 0; line-height: 1.6; }
.markdown-body strong { font-weight: 700; color: #111827; }
.markdown-body em { font-style: italic; }
.markdown-body blockquote { border-left: 3px solid #d1d5db; margin: 6px 0; padding: 2px 0 2px 10px; color: #6b7280; }
.markdown-body hr { border: none; border-top: 1px solid #e5e7eb; margin: 10px 0; }
.markdown-body table { border-collapse: collapse; width: 100%; font-size: 12px; margin: 6px 0; }
.markdown-body th, .markdown-body td { border: 1px solid #e5e7eb; padding: 4px 8px; text-align: left; }
.markdown-body th { background: #f9fafb; font-weight: 600; }
.markdown-body a { color: #3b82f6; text-decoration: underline; }
</style>
