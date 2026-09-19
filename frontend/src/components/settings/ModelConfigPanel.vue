<template>
  <div class="config-panel">
    <div class="config-header">
      <button class="back-btn" @click="emit('close')">← 返回</button>
      <span class="config-title">渠道与模型配置</span>
      <button class="save-btn" @click="save">保存</button>
    </div>

    <div v-if="localConfig" class="config-body">
      <!-- 快速添加预设 -->
      <div class="section-title">快速添加预设</div>
      <div class="preset-row">
        <button
          v-for="preset in PROVIDER_PRESETS"
          :key="preset.id"
          class="preset-btn"
          :class="{ added: isAdded(preset.id) }"
          :disabled="isAdded(preset.id)"
          @click="addPreset(preset)"
        >
          <span class="preset-name">{{ preset.name }}</span>
          <span class="preset-tag">{{ isAdded(preset.id) ? '已添加' : '+ 添加' }}</span>
        </button>
      </div>

      <!-- 已配置 Providers -->
      <div class="section-title" style="margin-top:24px">已配置渠道</div>
      <div v-if="localConfig.providers.length === 0" class="empty-providers">
        暂无渠道，请从预设添加或自定义
      </div>
      <div v-for="(p, idx) in localConfig.providers" :key="p.id" class="provider-block">
        <div class="provider-header">
          <span class="provider-name">{{ p.name || '未命名' }}</span>
          <button class="del-provider-btn" title="删除" @click="removeProvider(idx)">✕</button>
        </div>
        <div class="row">
          <label>名称</label>
          <input v-model="p.name" />
        </div>
        <div class="row">
          <label>Base URL</label>
          <input v-model="p.base_url" class="url-input" />
        </div>
        <div class="row">
          <label>API Key</label>
          <input v-model="p.api_key" type="password" placeholder="sk-..." />
        </div>
        <div class="row">
          <label>模型列表</label>
          <input
            v-model="modelsText[idx]"
            placeholder="用逗号分隔，如 qwen-plus, qwen-max"
            @blur="syncModels(idx)"
          />
        </div>
        <div class="row">
          <label>Context Limit</label>
          <input
            type="number"
            v-model.number="p.context_limit"
            placeholder="如 128000（留空则不自动摘要）"
          />
        </div>
      </div>

      <button class="add-custom-btn" @click="addCustom">+ 自定义渠道</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { ModelsConfig, Provider } from '../../types'
import { useModelsStore } from '../../stores/models'

const emit = defineEmits<{ close: [] }>()
const store = useModelsStore()

const PROVIDER_PRESETS: Omit<Provider, 'api_key'>[] = [
  {
    id: 'aliyun_qwen',
    name: '阿里百炼',
    type: 'openai_compat',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen-plus', 'qwen-max', 'qwen-turbo', 'qwen-long'],
  },
  {
    id: 'mimo_sub',
    name: 'MiMo (订阅版)',
    type: 'openai_compat',
    base_url: 'https://token-plan-cn.xiaomimimo.com/v1',
    models: ['MiMo-7B-RL'],
  },
  {
    id: 'mimo_free',
    name: 'MiMo (非订阅版)',
    type: 'openai_compat',
    base_url: 'https://api.xiaomimimo.com/v1',
    models: ['MiMo-7B-RL'],
  },
]

const localConfig = ref<ModelsConfig | null>(null)
const modelsText = ref<string[]>([])

watch(
  () => store.config,
  (cfg) => {
    if (!cfg) return
    localConfig.value = JSON.parse(JSON.stringify(cfg))
    modelsText.value = cfg.providers.map((p: Provider) => p.models.join(', '))
  },
  { immediate: true },
)

onMounted(async () => {
  await store.load()
})

function isAdded(presetId: string): boolean {
  return !!localConfig.value?.providers.find((p) => p.id === presetId)
}

function addPreset(preset: Omit<Provider, 'api_key'>) {
  if (!localConfig.value || isAdded(preset.id)) return
  const newProvider: Provider = { ...preset, api_key: '' }
  localConfig.value.providers.push(newProvider)
  modelsText.value.push(preset.models.join(', '))
}

function addCustom() {
  if (!localConfig.value) return
  const id = `custom_${Date.now()}`
  localConfig.value.providers.push({
    id,
    name: '自定义',
    type: 'openai_compat',
    base_url: '',
    api_key: '',
    models: [],
  })
  modelsText.value.push('')
}

function removeProvider(idx: number) {
  if (!localConfig.value) return
  const removed = localConfig.value.providers[idx]
  localConfig.value.providers.splice(idx, 1)
  modelsText.value.splice(idx, 1)
  if (localConfig.value.default_model.provider_id === removed.id) {
    const first = localConfig.value.providers[0]
    if (first) {
      localConfig.value.default_model.provider_id = first.id
      localConfig.value.default_model.model = first.models[0] ?? ''
    }
  }
  if (localConfig.value.summary_model?.provider_id === removed.id) {
    localConfig.value.summary_model = { ...localConfig.value.default_model }
  }
}

function syncModels(idx: number) {
  if (!localConfig.value) return
  localConfig.value.providers[idx].models = modelsText.value[idx]
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

async function save() {
  if (!localConfig.value) return
  modelsText.value.forEach((_, idx) => syncModels(idx))
  await store.save(localConfig.value)
  emit('close')
}
</script>

<style scoped>
.config-panel {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: #faf9f7;
  display: flex;
  flex-direction: column;
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e0dcd5;
  flex-shrink: 0;
}

.config-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.back-btn {
  background: none;
  border: 1px solid #e0dcd5;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  font-family: inherit;
}
.back-btn:hover { background: #f0ede8; }

.save-btn {
  background: #5b6e8a;
  border: none;
  color: #ffffff;
  border-radius: 6px;
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}
.save-btn:hover { background: #4a5c6b; }

.config-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 640px;
  margin: 0 auto;
  width: 100%;
}
.config-body::-webkit-scrollbar { width: 4px; }
.config-body::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

.section-title {
  font-size: 11px;
  font-weight: 700;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.row label {
  width: 80px;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}
.row input, .row select {
  flex: 1;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  font-size: 13px;
  padding: 6px 10px;
  font-family: inherit;
  min-width: 0;
}
.row input:focus, .row select:focus { outline: none; border-color: #5b6e8a; }
.url-input { font-size: 11px; color: #6b7280; }

.preset-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 8px 12px;
  border: 1.5px solid #e0dcd5;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
  min-width: 110px;
}
.preset-btn:hover:not(:disabled) { border-color: #5b6e8a; background: #f0f4fa; }
.preset-btn.added, .preset-btn:disabled {
  border-color: #d1d5db; background: #f9fafb; cursor: default; opacity: 0.6;
}
.preset-name { font-size: 13px; font-weight: 600; color: #1a1a1a; }
.preset-tag { font-size: 11px; color: #5b6e8a; }
.preset-btn.added .preset-tag { color: #9ca3af; }

.provider-block {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.provider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.provider-name { font-size: 14px; font-weight: 600; color: #374151; }
.del-provider-btn {
  background: none; border: none; color: #d1d5db;
  cursor: pointer; font-size: 12px; padding: 2px 6px; border-radius: 4px;
}
.del-provider-btn:hover { background: #fee2e2; color: #ef4444; }

.empty-providers {
  text-align: center; color: #9ca3af; font-size: 13px; padding: 24px 0;
}

.add-custom-btn {
  width: 100%;
  margin-top: 8px;
  padding: 10px;
  border: 1.5px dashed #d1d5db;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.add-custom-btn:hover { border-color: #5b6e8a; color: #5b6e8a; background: #f0f4fa; }
</style>
