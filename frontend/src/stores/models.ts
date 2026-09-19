import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ModelsConfig } from '../types'
import { api } from '../api'

export const useModelsStore = defineStore('models', () => {
  const config = ref<ModelsConfig | null>(null)

  async function load() {
    config.value = await api.getModels()
  }

  async function save(newConfig: ModelsConfig) {
    await api.saveModels(newConfig)
    config.value = newConfig
  }

  function getDefaultProviderAndModel() {
    if (!config.value) return { provider_id: '', model: '' }
    return config.value.default_model
  }

  // 根据模型名找到它所属的 provider_id；找不到则回退到默认 provider
  function getProviderForModel(model: string): string {
    if (!config.value) return ''
    const provider = config.value.providers.find((p) => p.models.includes(model))
    return provider?.id ?? config.value.default_model.provider_id
  }

  return { config, load, save, getDefaultProviderAndModel, getProviderForModel }
})
