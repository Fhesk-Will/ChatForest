<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <span>模型配置</span>
        <button @click="emit('close')">✕</button>
      </div>

      <div v-if="localConfig" class="modal-body">

        <!-- 默认模型 -->
        <div class="section-title">默认模型</div>
        <div class="row">
          <label>Provider</label>
          <select v-model="localConfig.default_model.provider_id" @change="onDefaultProviderChange">
            <option v-for="p in localConfig.providers" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="row">
          <label>Model</label>
          <select v-model="localConfig.default_model.model">
            <option v-for="m in currentProviderModels" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- 自动摘要设置 -->
        <div class="section-title" style="margin-top:20px">自动摘要</div>
        <div class="row">
          <label>摘要模型</label>
          <select v-model="localConfig.summary_model!.provider_id" @change="onSummaryProviderChange" style="flex:0.6">
            <option v-for="p in localConfig.providers" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <select v-model="localConfig.summary_model!.model" style="flex:1">
            <option v-for="m in summaryProviderModels" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="row">
          <label>触发阈值</label>
          <input
            type="range" min="0.5" max="1.0" step="0.05"
            v-model.number="localConfig.auto_summary_threshold"
            style="flex:1"
          />
          <span class="threshold-label">{{ Math.round((localConfig.auto_summary_threshold ?? 0.8) * 100) }}%</span>
        </div>
        <div class="row">
          <label>保留消息数</label>
          <input
            type="number" min="2" max="20"
            v-model.number="localConfig.auto_summary_keep_recent"
            style="width:80px;flex:none"
          />
          <span class="hint-text">条（触发时保留最近 N 条不压缩）</span>
        </div>
        <div class="row" style="align-items:flex-start">
          <label style="padding-top:6px">摘要提示词</label>
          <textarea
            v-model="localConfig.summary_prompt"
            class="summary-prompt-input"
            rows="3"
            placeholder="请对以上对话内容进行简洁的摘要，保留关键事实、决策和继续对话所需的上下文。用第三人称、过去时态书写，不超过500字。"
          ></textarea>
        </div>

        <!-- 跳转到详细配置 -->
        <button class="open-config-btn" @click="emit('openModelConfig')">
          渠道与模型详细配置 →
        </button>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" @click="emit('close')">取消</button>
        <button class="save-btn" @click="save">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { ModelsConfig, Provider } from '../../types'
import { useModelsStore } from '../../stores/models'

const emit = defineEmits<{ close: []; openModelConfig: [] }>()
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
    // 初始化可选字段的默认值
    if (!localConfig.value!.summary_model) {
      localConfig.value!.summary_model = { ...localConfig.value!.default_model }
    }
    if (localConfig.value!.auto_summary_threshold === undefined) {
      localConfig.value!.auto_summary_threshold = 0.8
    }
    if (localConfig.value!.auto_summary_keep_recent === undefined) {
      localConfig.value!.auto_summary_keep_recent = 4
    }
    if (localConfig.value!.summary_prompt === undefined) {
      localConfig.value!.summary_prompt = ''
    }
  },
  { immediate: true },
)

onMounted(async () => {
  await store.load()
})

const currentProviderModels = computed(() => {
  if (!localConfig.value) return []
  const p = localConfig.value.providers.find(
    (prov) => prov.id === localConfig.value!.default_model.provider_id,
  )
  return p?.models ?? []
})

const summaryProviderModels = computed(() => {
  if (!localConfig.value?.summary_model) return []
  const p = localConfig.value.providers.find(
    (prov) => prov.id === localConfig.value!.summary_model!.provider_id,
  )
  return p?.models ?? []
})

function onDefaultProviderChange() {
  if (!localConfig.value) return
  const models = currentProviderModels.value
  if (models.length > 0) localConfig.value.default_model.model = models[0]
}

function onSummaryProviderChange() {
  if (!localConfig.value?.summary_model) return
  const models = summaryProviderModels.value
  if (models.length > 0) localConfig.value.summary_model.model = models[0]
}

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
  // If removed provider was the default, reset to first available
  if (localConfig.value.default_model.provider_id === removed.id) {
    const first = localConfig.value.providers[0]
    if (first) {
      localConfig.value.default_model.provider_id = first.id
      localConfig.value.default_model.model = first.models[0] ?? ''
    }
  }
  // If removed provider was the summary model, reset to default
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
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,0.14);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  flex-shrink: 0;
}
.modal-header button {
  background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 14px;
}
.modal-header button:hover { color: #374151; }

.modal-body {
  padding: 18px;
  overflow-y: auto;
  flex: 1;
}
.modal-body::-webkit-scrollbar { width: 4px; }
.modal-body::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

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
  width: 72px;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}
.row input, .row select {
  flex: 1;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  font-size: 13px;
  padding: 5px 8px;
  font-family: inherit;
  min-width: 0;
}
.row input:focus, .row select:focus { outline: none; border-color: #5b6e8a; background: #fff; }
.url-input { font-size: 11px; color: #6b7280; }

/* Preset buttons */
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
.preset-btn:hover:not(:disabled) {
  border-color: #5b6e8a;
  background: #f0f4fa;
}
.preset-btn.added, .preset-btn:disabled {
  border-color: #d1d5db;
  background: #f9fafb;
  cursor: default;
  opacity: 0.6;
}
.preset-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
}
.preset-tag {
  font-size: 11px;
  color: #5b6e8a;
}
.preset-btn.added .preset-tag { color: #9ca3af; }

/* Provider blocks */
.provider-block {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.provider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.provider-name {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.del-provider-btn {
  background: none;
  border: none;
  color: #d1d5db;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}
.del-provider-btn:hover { background: #fee2e2; color: #ef4444; }

.empty-providers {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 16px 0;
}

.add-custom-btn {
  width: 100%;
  margin-top: 4px;
  padding: 8px;
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

.open-config-btn {
  width: 100%;
  margin-top: 16px;
  padding: 10px;
  border: 1.5px solid #5b6e8a;
  border-radius: 8px;
  background: transparent;
  color: #5b6e8a;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.open-config-btn:hover { background: #f0f4fa; }

.threshold-label {
  font-size: 12px;
  color: #6b7280;
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.hint-text {
  font-size: 11px;
  color: #9ca3af;
  flex-shrink: 0;
}

.summary-prompt-input {
  flex: 1;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  font-size: 12px;
  padding: 6px 8px;
  font-family: inherit;
  resize: vertical;
  min-height: 56px;
  line-height: 1.5;
}
.summary-prompt-input:focus { outline: none; border-color: #5b6e8a; background: #fff; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.cancel-btn {
  background: #f3f4f6; border: 1px solid #e5e7eb; color: #374151;
  border-radius: 6px; padding: 7px 16px; font-size: 13px; cursor: pointer; font-family: inherit;
}
.cancel-btn:hover { background: #e5e7eb; }
.save-btn {
  background: #5b6e8a; border: none; color: #ffffff;
  border-radius: 6px; padding: 7px 16px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit;
}
.save-btn:hover { background: #4a5c6b; }
</style>
