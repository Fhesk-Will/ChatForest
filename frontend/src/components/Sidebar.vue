<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <button class="new-btn" @click="emit('new-canvas')">🌱 新画布</button>
    </div>

    <div class="canvas-list">
      <div
        v-for="item in canvasList"
        :key="item.id"
        class="canvas-item"
        :class="{ active: item.id === activeId }"
        @click="emit('select', item.id)"
      >
        <span class="canvas-title">{{ item.title }}</span>
        <button
          class="del-btn"
          title="删除"
          @click.stop="emit('delete', item.id)"
        >✕</button>
      </div>
      <div v-if="canvasList.length === 0" class="empty-hint">暂无画布</div>
    </div>

    <div class="sidebar-footer">
      <button class="settings-btn" @click="emit('open-settings')">⚙ 模型配置</button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { CanvasSummary } from '../types'

defineProps<{
  canvasList: CanvasSummary[]
  activeId: string | null
}>()

const emit = defineEmits<{
  'new-canvas': []
  select: [id: string]
  delete: [id: string]
  'open-settings': []
}>()
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #faf9f7;
  border-right: 1px solid #e0dcd5;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-shadow: 1px 0 3px rgba(0,0,0,0.04);
  z-index: 10;
}

.sidebar-header {
  padding: 16px 14px 12px;
  border-bottom: 1px solid #ebe7e1;
}

.new-btn {
  width: 100%;
  padding: 9px 16px;
  border-radius: 24px;
  border: 1.5px solid #e0dcd5;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #1a1a1a;
  transition: all 0.15s;
  font-family: inherit;
}
.new-btn:hover {
  background: #f5f3f0;
  border-color: #8a9db5;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.canvas-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.canvas-list::-webkit-scrollbar { width: 3px; }
.canvas-list::-webkit-scrollbar-track { background: transparent; }
.canvas-list::-webkit-scrollbar-thumb { background: #d1cdc7; border-radius: 2px; }

.canvas-item {
  display: flex;
  align-items: center;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  gap: 6px;
  transition: all 0.15s;
}
.canvas-item:hover {
  background: #fff;
  border-color: #ebe7e1;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.canvas-item.active {
  background: #fff;
  border-color: #8a9db5;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.canvas-title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.canvas-item.active .canvas-title { font-weight: 600; }

.del-btn {
  background: none;
  border: none;
  color: #bbb;
  cursor: pointer;
  font-size: 11px;
  padding: 2px 5px;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.15s;
  flex-shrink: 0;
}
.canvas-item:hover .del-btn { opacity: 1; }
.del-btn:hover { background: #fee2e2; color: #ef4444; }

.empty-hint {
  text-align: center;
  color: #bbb;
  font-size: 12px;
  padding: 24px 0;
}

.sidebar-footer {
  padding: 12px 14px;
  border-top: 1px solid #ebe7e1;
}

.settings-btn {
  width: 100%;
  background: #fff;
  border: 1px solid #ebe7e1;
  color: #5c5c5c;
  border-radius: 24px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  font-family: inherit;
}
.settings-btn:hover {
  background: #f5f3f0;
  color: #1a1a1a;
  border-color: #8a9db5;
}
</style>
