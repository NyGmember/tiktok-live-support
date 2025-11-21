<template>
  <div 
    class="flex items-center justify-between p-3 mb-2 rounded-lg shadow-sm transition-all duration-500"
    :class="[
      rank === 1 ? 'bg-yellow-500/20 border border-yellow-500/50' : 
      rank === 2 ? 'bg-gray-400/20 border border-gray-400/50' : 
      rank === 3 ? 'bg-orange-500/20 border border-orange-500/50' : 
      'bg-slate-800/50 border border-slate-700'
    ]"
  >
    <div class="flex items-center gap-3">
      <!-- Rank Badge -->
      <div 
        class="flex items-center justify-center w-8 h-8 font-bold rounded-full"
        :class="[
          rank === 1 ? 'bg-yellow-500 text-black' : 
          rank === 2 ? 'bg-gray-400 text-black' : 
          rank === 3 ? 'bg-orange-500 text-black' : 
          'bg-slate-700 text-slate-300'
        ]"
      >
        {{ rank }}
      </div>
      
      <!-- User Info -->
      <div class="flex flex-col">
        <span class="font-bold text-white truncate max-w-[150px]">{{ nickname }}</span>
        <span class="text-xs text-slate-400">ID: {{ userId }}</span>
      </div>
    </div>

    <!-- Score -->
    <div class="text-right">
      <div class="text-xl font-black text-white tabular-nums">
        {{ Math.floor(score).toLocaleString() }}
      </div>
      <div class="text-xs text-slate-400">points</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  rank: Number,
  nickname: String,
  userId: String,
  score: Number
})
</script>
