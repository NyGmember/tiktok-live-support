<template>
  <div class="py-1 border-b border-slate-700/50 last:border-0 font-mono text-sm">
    <span class="text-slate-500 mr-2">[{{ timestamp }}]</span>
    <span 
      class="font-bold mr-2"
      :class="{
        'text-green-400': level === 'INFO',
        'text-yellow-400': level === 'WARNING',
        'text-red-400': level === 'ERROR'
      }"
    >
      {{ level }}
    </span>
    <span class="text-slate-300">{{ message }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  log: Object
})

const timestamp = computed(() => {
  if (!props.log.timestamp) return ''
  return new Date(props.log.timestamp).toLocaleTimeString()
})

const level = computed(() => props.log.level || 'INFO')
const message = computed(() => props.log.message || '')
</script>
