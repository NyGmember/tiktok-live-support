<template>
  <div class="w-screen h-screen overflow-hidden p-8 flex flex-col items-end">
    <!-- Title / Header -->
    <div class="mb-6 text-right">
      <h1 class="text-4xl font-black text-white drop-shadow-[0_4px_4px_rgba(0,0,0,0.8)] uppercase tracking-wider italic">
        Live Leaderboard
      </h1>
      <div class="text-xl text-yellow-400 font-bold drop-shadow-md">
        Top 5 Scorers
      </div>
    </div>

    <!-- Leaderboard List -->
    <div class="w-[400px] relative">
      <TransitionGroup name="list" tag="div" class="flex flex-col gap-3">
        <div 
          v-for="(user, index) in store.leaderboard" 
          :key="user.user_key"
          class="relative transform transition-all duration-500"
        >
          <div 
            class="flex items-center justify-between p-4 rounded-xl shadow-lg backdrop-blur-md border-l-4"
            :class="[
              index === 0 ? 'bg-yellow-900/80 border-yellow-500' : 
              index === 1 ? 'bg-slate-800/80 border-gray-400' : 
              index === 2 ? 'bg-orange-900/80 border-orange-500' : 
              'bg-slate-900/80 border-slate-600'
            ]"
          >
            <!-- Rank & Info -->
            <div class="flex items-center gap-4">
              <div 
                class="w-10 h-10 flex items-center justify-center rounded-full font-black text-xl shadow-inner"
                :class="[
                  index === 0 ? 'bg-gradient-to-br from-yellow-300 to-yellow-600 text-white' : 
                  index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-600 text-white' : 
                  index === 2 ? 'bg-gradient-to-br from-orange-300 to-orange-600 text-white' : 
                  'bg-slate-700 text-slate-300'
                ]"
              >
                {{ index + 1 }}
              </div>
              
              <div class="flex flex-col">
                <span class="text-white font-bold text-lg drop-shadow-md truncate max-w-[180px]">
                  {{ user.user_key.split('|')[1] }}
                </span>
              </div>
            </div>

            <!-- Score -->
            <div class="text-right">
              <div class="text-2xl font-black text-white tabular-nums drop-shadow-md">
                {{ Math.floor(user.score).toLocaleString() }}
              </div>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'

const store = useGameStore()

onMounted(() => {
  store.connectWebSocket()
})
</script>

<style scoped>
/* List Transitions */
.list-move, /* apply transition to moving elements */
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* Ensure leaving items are taken out of layout flow so others move up smoothly */
.list-leave-active {
  position: absolute;
  width: 100%;
}
</style>
