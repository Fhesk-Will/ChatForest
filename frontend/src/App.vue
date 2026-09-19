<template>
  <div class="app-layout">
    <Sidebar
      :canvas-list="canvasList"
      :active-id="activeCanvasId"
      @new-canvas="createCanvas"
      @select="selectCanvas"
      @delete="deleteCanvas"
      @open-settings="showSettings = true"
    />

    <main class="main-area">
      <!-- 顶部导航栏 -->
      <nav v-if="activeCanvasId && !backendError" class="navbar">
        <div class="navbar-left">
          <div class="logo-icon"><img src="/logo.png" alt="logo" class="logo-img" /></div>
          <span class="logo-text">{{ canvasStore.currentCanvas?.title || '未命名画布' }}</span>
        </div>

        <div class="mode-switcher">
          <button
            class="mode-btn"
            :class="{ active: mode === 'focus' }"
            @click="mode = 'focus'"
          >💬 专注模式</button>
          <button
            class="mode-btn"
            :class="{ active: mode === 'overview' }"
            @click="mode = 'overview'"
          >🔀 总览模式</button>
        </div>

        <div class="navbar-right">
          <span v-if="canvasStore.saving" class="saving-hint">保存中…</span>
        </div>
      </nav>

      <!-- 内容区 -->
      <div class="content-area">
        <div v-if="backendError" class="empty-state">
          <div class="empty-icon">⚠</div>
          <div class="empty-text">无法连接后端，请启动后端服务</div>
          <code style="color:#9ca3af;font-size:12px">bash service.sh start</code>
        </div>
        <div v-else-if="!activeCanvasId" class="empty-state">
          <div class="empty-icon">✦</div>
          <div class="empty-text">点击左侧「+ 新画布」开始</div>
        </div>
        <template v-else>
          <!-- 总览模式 -->
          <CanvasBoard
            v-show="mode === 'overview'"
            ref="canvasBoardRef"
            :key="activeCanvasId"
          />
          <!-- 专注模式 -->
          <FocusMode
            v-show="mode === 'focus'"
            ref="focusModeRef"
            @send="onFocusSend"
            @remove-node="onFocusRemoveNode"
            @retry-node="onFocusRetryNode"
          />
        </template>
      </div>
    </main>

    <ModelSettings v-if="showSettings" @close="showSettings = false" @open-model-config="showSettings = false; showModelConfig = true" />
    <ModelConfigPanel v-if="showModelConfig" @close="showModelConfig = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Sidebar from './components/Sidebar.vue'
import CanvasBoard from './components/canvas/CanvasBoard.vue'
import FocusMode from './components/canvas/FocusMode.vue'
import ModelSettings from './components/settings/ModelSettings.vue'
import ModelConfigPanel from './components/settings/ModelConfigPanel.vue'
import { useCanvasStore } from './stores/canvas'
import { useModelsStore } from './stores/models'
import { api } from './api'
import type { CanvasSummary } from './types'

const canvasStore = useCanvasStore()
const modelsStore = useModelsStore()

const canvasList = ref<CanvasSummary[]>([])
const activeCanvasId = ref<string | null>(null)
const showSettings = ref(false)
const showModelConfig = ref(false)
const backendError = ref(false)
const mode = ref<'overview' | 'focus'>('overview')

const canvasBoardRef = ref<InstanceType<typeof CanvasBoard> | null>(null)
const focusModeRef = ref<InstanceType<typeof FocusMode> | null>(null)

// 同步 canvas 标题变化到侧边栏列表
watch(() => canvasStore.currentCanvas?.title, (title) => {
  if (!title || !activeCanvasId.value) return
  const item = canvasList.value.find((c) => c.id === activeCanvasId.value)
  if (item) item.title = title
})

onMounted(async () => {
  try {
    await modelsStore.load()
    canvasList.value = await api.listCanvases()
    backendError.value = false
    if (canvasList.value.length > 0) {
      await selectCanvas(canvasList.value[0].id)
    }
  } catch {
    backendError.value = true
  }
})

async function createCanvas() {
  try {
    const canvas = await api.createCanvas()
    canvasList.value.unshift({ id: canvas.id, title: canvas.title, updated_at: canvas.updated_at })
    await selectCanvas(canvas.id)
  } catch {
    alert('无法连接后端，请确认后端服务已启动')
  }
}

async function selectCanvas(id: string) {
  const canvas = await api.getCanvas(id)
  canvasStore.loadCanvas(canvas)
  activeCanvasId.value = id
}

async function deleteCanvas(id: string) {
  if (!confirm('确认删除此画布？')) return
  await api.deleteCanvas(id)
  canvasList.value = canvasList.value.filter((c) => c.id !== id)
  if (activeCanvasId.value === id) {
    activeCanvasId.value = canvasList.value[0]?.id ?? null
    if (activeCanvasId.value) await selectCanvas(activeCanvasId.value)
    else canvasStore.loadCanvas({ id: '', title: '', created_at: '', updated_at: '', cards: [], edges: [] })
  }
}

async function onFocusSend(parentId: string | null, text: string, model: string) {
  await canvasBoardRef.value?.sendMessage(parentId, text, model)
}

function onFocusRemoveNode(nodeId: string) {
  canvasStore.removeCard(nodeId)
}

async function onFocusRetryNode(nodeId: string, _userMsg: string, model: string) {
  await canvasBoardRef.value?.retryMessage(nodeId, model)
}
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #f5f3f0;
  color: #1a1a1a;
  font-family: 'Inter', 'SF Pro Display', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

#app { height: 100vh; }
</style>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* Navbar */
.navbar {
  height: 52px;
  background: rgba(255,255,255,0.92);
  border-bottom: 1px solid #e0dcd5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 100;
  flex-shrink: 0;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 160px;
}

.logo-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #6b7d8e, #4a5c6b);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  overflow: hidden; /* 让 logo 图片遵循圆角裁切 */
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-text {
  font-weight: 600;
  font-size: 14px;
  color: #1a1a1a;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-switcher {
  display: flex;
  background: #f0ede8;
  border-radius: 24px;
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  padding: 7px 16px;
  border-radius: 22px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #5c5c5c;
  transition: all 0.15s;
  white-space: nowrap;
  font-family: inherit;
}
.mode-btn.active {
  background: #fff;
  color: #1a1a1a;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  font-weight: 600;
}
.mode-btn:hover:not(.active) {
  color: #1a1a1a;
  background: rgba(255,255,255,0.5);
}

.navbar-right {
  min-width: 160px;
  display: flex;
  justify-content: flex-end;
}

.saving-hint {
  font-size: 12px;
  color: #999;
}

/* Content area */
.content-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #9ca3af;
}

.empty-icon { font-size: 48px; }
.empty-text { font-size: 15px; }
</style>
