<template>
  <div class="toolbar">
    <button class="toolbar-btn primary" @click="emit('new-card')">+ 新消息</button>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ 'new-card': [] }>()
</script>

<style scoped>
.toolbar {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  gap: 8px;
}
.toolbar-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
  border-radius: 8px;
  padding: 7px 16px;
  font-size: 13px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.toolbar-btn:hover { background: #f3f4f6; }
.toolbar-btn.primary { background: #3b82f6; color: #ffffff; border-color: #3b82f6; font-weight: 600; }
.toolbar-btn.primary:hover { background: #2563eb; }
</style>
