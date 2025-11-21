<template>
  <div class="min-h-screen bg-slate-900 text-white p-6">
    <header class="flex items-center justify-between mb-8 pb-4 border-b border-slate-700">
      <div>
        <h1 class="text-3xl font-bold bg-gradient-to-r from-pink-500 to-violet-500 bg-clip-text text-transparent">
          TikTok Live Admin
        </h1>
        <p class="text-slate-400 mt-1">Control Panel & Analytics</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700">
          <div class="w-2 h-2 rounded-full" :class="store.isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></div>
          <span class="text-sm font-medium">{{ store.isConnected ? 'Connected' : 'Disconnected' }}</span>
        </div>
        <div class="text-sm text-slate-400">
          Session: <span class="text-white font-mono">{{ store.currentSessionId }}</span>
        </div>
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Controls -->
      <div class="space-y-6">
        <!-- Connection Control -->
        <div class="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
            <span class="text-pink-500">📡</span> Stream Connection
          </h2>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-slate-400 mb-1">Target TikTok ID</label>
              <input 
                v-model="targetId" 
                type="text" 
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-500 transition-colors"
                placeholder="@username"
              >
            </div>
            
            <div class="flex gap-2">
              <button 
                @click="handleStart('live')"
                :disabled="store.isConnected"
                class="flex-1 bg-pink-600 hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg transition-colors"
              >
                Start Live
              </button>
              <button 
                @click="handleStart('mock')"
                :disabled="store.isConnected"
                class="flex-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg transition-colors"
              >
                Start Mock
              </button>
            </div>
            
            <button 
              @click="store.stopStream()"
              :disabled="!store.isConnected"
              class="w-full bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg transition-colors"
            >
              Stop Stream
            </button>
          </div>
        </div>

        <!-- Session Control -->
        <div class="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
            <span class="text-violet-500">🎮</span> Game Control
          </h2>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-slate-400 mb-1">New Session ID</label>
              <div class="flex gap-2">
                <input 
                  v-model="newSessionId" 
                  type="text" 
                  class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-violet-500 transition-colors"
                  placeholder="Session Name"
                >
                <button 
                  @click="handleReset"
                  class="bg-violet-600 hover:bg-violet-700 text-white font-bold px-4 rounded-lg transition-colors"
                >
                  Set
                </button>
              </div>
            </div>

            <hr class="border-slate-700 my-4">

            <button 
              @click="handleSelectWinner"
              class="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-4 rounded-lg shadow-lg shadow-yellow-500/20 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
            >
              🏆 Select Winner
            </button>
          </div>
        </div>
      </div>

      <!-- Middle Column: Leaderboard Preview -->
      <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 flex flex-col h-[600px]">
        <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
          <span class="text-yellow-500">📊</span> Live Leaderboard
        </h2>
        
        <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
          <LeaderboardItem 
            v-for="(user, index) in store.leaderboard" 
            :key="user.user_key"
            :rank="index + 1"
            :nickname="user.user_key.split('|')[1]"
            :user-id="user.user_key.split('|')[0]"
            :score="user.score"
          />
          
          <div v-if="store.leaderboard.length === 0" class="text-center text-slate-500 py-10">
            Waiting for data...
          </div>
        </div>
      </div>

      <!-- Right Column: Logs -->
      <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 flex flex-col h-[600px]">
        <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
          <span class="text-blue-500">📝</span> System Logs
        </h2>
        
        <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar bg-slate-900/50 rounded-lg p-4 font-mono text-sm">
          <LogItem 
            v-for="(log, index) in store.logs" 
            :key="index" 
            :log="log" 
          />
        </div>
      </div>
    </div>

    <!-- Winner Modal -->
    <div v-if="winner" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-slate-800 border border-yellow-500/50 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl shadow-yellow-500/20 transform scale-100 animate-bounce-in">
        <div class="text-6xl mb-4">👑</div>
        <h2 class="text-3xl font-black text-white mb-2">WINNER!</h2>
        <div class="text-2xl text-yellow-400 font-bold mb-6">{{ winner.nickname }}</div>
        
        <div class="bg-slate-900/50 rounded-xl p-4 mb-6 text-left space-y-2">
          <div class="flex justify-between">
            <span class="text-slate-400">Score</span>
            <span class="font-bold text-white">{{ winner.score }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Comments</span>
            <span class="font-bold text-white">{{ winner.comments.length }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Gifts</span>
            <span class="font-bold text-white">{{ winner.stats.total_gifts_sent || 0 }}</span>
          </div>
        </div>

        <button 
          @click="winner = null"
          class="w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'
import LeaderboardItem from '../components/LeaderboardItem.vue'
import LogItem from '../components/LogItem.vue'

const store = useGameStore()
const targetId = ref('@juneang2004')
const newSessionId = ref('')
const winner = ref(null)

onMounted(() => {
  store.fetchStatus()
  store.connectWebSocket()
})

const handleStart = (mode) => {
  if (!targetId.value) return alert('Please enter a TikTok ID')
  store.startStream(targetId.value, mode)
}

const handleReset = () => {
  if (!newSessionId.value) return alert('Please enter a Session ID')
  store.resetSession(newSessionId.value)
  newSessionId.value = ''
}

const handleSelectWinner = async () => {
  const result = await store.selectWinner()
  if (result) {
    winner.value = result
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.5);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.8);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 1);
}

@keyframes bounce-in {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.05); }
  70% { transform: scale(0.9); }
  100% { transform: scale(1); opacity: 1; }
}
.animate-bounce-in {
  animation: bounce-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}
</style>
