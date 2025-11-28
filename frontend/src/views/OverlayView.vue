<template>
  <div class="w-screen h-screen bg-[#00FF00] overflow-hidden p-8 flex flex-col items-start">
    <!-- Header -->
    <div class="mb-4 bg-white backdrop-blur-sm rounded-xl p-4 shadow-lg border-l-4 border-blue-500 w-[250px]">
      <h1 class="text-xl font-black text-gray-800 uppercase tracking-wider italic">
        🏆 Leaderboard
      </h1>
      <div class="text-sm text-gray-600 font-bold mt-1">
        Users: <span class="text-blue-600 text-lg">{{ activeUserCount[0] }}</span><span class="text-blue-400 text-md"> / {{ activeUserCount[1] }}</span>
      </div>
    </div>

    <!-- Leaderboard List -->
    <div class="w-[250px] relative">
      <TransitionGroup name="list" tag="div" class="flex flex-col gap-2">
        <div
          v-for="(user, index) in top5Users"
          :key="user.user_id"
          class="relative transform transition-all duration-500"
        >
          <div
            class="flex items-center p-2 rounded-xl shadow-lg backdrop-blur-md border-2 bg-white"
            :class="[
              index === 0 ? 'border-yellow-400 ring-2 ring-yellow-200' : 
              index === 1 ? 'border-yellow-200' : 
              index === 2 ? 'border-orange-400' : 'border-blue-100'
            ]"
          >
            <!-- Rank / Avatar Section -->
            <div class="relative mr-3">
                <!-- Crown for 1st Place -->
                <div v-if="index === 0" class="absolute -top-4 -right-2 text-2xl z-20 filter drop-shadow-md animate-bounce-slow transform rotate-[30deg]">
                    👑
                </div>
                
                <!-- Rank Badge (for 2nd & 3rd) -->
                <div v-if="index === 1" class="absolute -top-2 -left-2 text-lg z-20">🥈</div>
                <div v-if="index === 2" class="absolute -top-2 -left-2 text-lg z-20">🥉</div>
                
                <!-- Rank Number (for 4th, 5th) -->
                <div v-if="index > 2" class="absolute -top-2 -left-2 w-5 h-5 bg-gray-700 text-white rounded-full flex items-center justify-center text-[10px] font-bold z-20 border-2 border-white">
                    {{ index + 1 }}
                </div>

                <!-- Avatar -->
                <img
                  :src="user.avatar_url || `https://ui-avatars.com/api/?name=${user.nickname}&background=random`"
                  class="w-10 h-10 rounded-full border-2 object-cover"
                  :class="[
                    index === 0 ? 'border-yellow-400' : 
                    index === 1 ? 'border-gray-300' : 
                    index === 2 ? 'border-orange-400' : 'border-gray-200'
                  ]"
                />
            </div>

            <!-- User Info -->
            <div class="flex-1 min-w-0 flex items-center justify-between">
                <h3 class="font-bold text-gray-900 truncate text-sm mr-2">
                  {{ user.nickname }}
                </h3>
                <span class="font-black text-blue-800 text-lg whitespace-nowrap">
                  <span v-if="user.score > 0">{{ user.score }}</span>
                  <span v-else>-</span>
                </span>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { config } from "../config";

const leaderboard = ref([]);
let ws = null;

const activeUserCount = computed(() => {
    return [leaderboard.value.filter(u => u.score > 0).length, leaderboard.value.length];
});

const top5Users = computed(() => {
    // Filter users with score > 0 first? Or just take top 5?
    // Usually leaderboard shows top scorers. 
    // Let's take top 5 from the raw list (which is already sorted by backend)
    // But maybe filter out 0 score if desired, though usually 0 score doesn't make it to top unless few players.
    // Let's just take top 5.
    return leaderboard.value.slice(0, 5).map(u => ({
        ...u,
        // Ensure avatar_url is present or handled in template
    }));
});

const connectWebSocket = () => {
  ws = new WebSocket(config.wsUrl);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.leaderboard) {
      leaderboard.value = data.leaderboard.map((item) => {
        const [id, name] = item.user_key.split("|", 2);
        return {
          user_id: id,
          nickname: name,
          score: item.score,
          avatar_url: item.avatar_url, // Backend needs to send this! If not, template handles fallback.
          comments: 0, 
          likes: 0,
          gifts: 0,
        };
      });
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 1000);
  };
};

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.5s cubic-bezier(0.55, 0, 0.1, 1);
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.list-leave-active {
  position: absolute;
  width: 100%;
}

@keyframes bounce-slow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-bounce-slow {
  animation: bounce-slow 2s infinite;
}
</style>
