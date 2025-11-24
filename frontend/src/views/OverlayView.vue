<template>
  <div class="w-screen h-screen overflow-hidden p-8 flex flex-col items-end">
    <!-- Title / Header -->
    <div class="mb-6 text-right">
      <h1
        class="text-4xl font-black text-white drop-shadow-[0_4px_4px_rgba(0,0,0,0.8)] uppercase tracking-wider italic"
      >
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
              index === 0
                ? 'bg-yellow-900/80 border-yellow-500'
                : index === 1
                ? 'bg-slate-800/80 border-gray-400'
                : index === 2
                ? 'bg-orange-900/80 border-orange-500'
                : 'bg-slate-900/80 border-slate-600',
            ]"
          >
            <!-- Rank & Info -->
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 flex items-center justify-center rounded-full font-black text-xl shadow-inner"
                :class="[
                  index === 0
                    ? 'bg-gradient-to-br from-yellow-300 to-yellow-600 text-white'
                    : index === 1
                    ? 'bg-gradient-to-br from-gray-300 to-gray-600 text-white'
                    : index === 2
                    ? 'bg-gradient-to-br from-orange-300 to-orange-600 text-white'
                    : 'bg-slate-700 text-slate-300',
                ]"
              >
                <template>
                  <div
                    class="w-screen h-screen bg-[#00FF00] overflow-hidden p-4"
                  >
                    <div class="max-w-md mx-auto">
                      <!-- Header -->
                      <div
                        class="bg-white/90 backdrop-blur-sm rounded-t-xl p-3 text-center shadow-lg mb-2"
                      >
                        <h1 class="text-xl font-bold text-gray-800">
                          Leaderboard
                        </h1>
                        <p class="text-sm text-gray-600 font-medium">
                          Total Participants: {{ leaderboard.length }}
                        </p>
                      </div>

                      <!-- Leaderboard List -->
                      <TransitionGroup name="list" tag="ul" class="space-y-2">
                        <li
                          v-for="(user, index) in filteredLeaderboard"
                          :key="user.user_id"
                          class="transform transition-all duration-500"
                        >
                          <div
                            class="bg-white/90 backdrop-blur-md rounded-xl p-2 shadow-lg flex items-center space-x-3 border-2"
                            :class="{
                              'border-yellow-400 scale-105 z-10': index === 0,
                              'border-gray-300': index === 1,
                              'border-orange-400': index === 2,
                              'border-transparent': index > 2,
                            }"
                          >
                            <!-- Rank/Avatar -->
                            <div class="relative flex-shrink-0">
                              <!-- Crown for Top 3 -->
                              <div
                                v-if="index < 3"
                                class="absolute -top-4 -left-2 w-8 h-8 z-20"
                              >
                                <span v-if="index === 0" class="text-2xl"
                                  >👑</span
                                >
                                <span v-if="index === 1" class="text-2xl"
                                  >🥈</span
                                >
                                <span v-if="index === 2" class="text-2xl"
                                  >🥉</span
                                >
                              </div>

                              <!-- Avatar -->
                              <div
                                class="w-12 h-12 rounded-full border-2 border-white shadow overflow-hidden bg-gray-200"
                              >
                                <!-- Placeholder if no avatar, or use user.avatar_url if available -->
                                <img
                                  :src="
                                    user.avatar_url ||
                                    `https://ui-avatars.com/api/?name=${user.nickname}&background=random`
                                  "
                                  class="w-full h-full object-cover"
                                />
                              </div>
                            </div>

                            <!-- User Info -->
                            <div class="flex-1 min-w-0">
                              <div class="flex justify-between items-baseline">
                                <h3
                                  class="font-bold text-gray-900 truncate text-sm"
                                >
                                  {{ user.nickname }}
                                </h3>
                                <span
                                  class="font-black text-blue-600 text-lg"
                                  >{{ user.score }}</span
                                >
                              </div>

                              <!-- Stats Icons -->
                              <div
                                class="flex items-center space-x-3 text-xs text-gray-600 mt-1"
                              >
                                <span class="flex items-center"
                                  ><span class="mr-1">💬</span>
                                  {{ user.comments }}</span
                                >
                                <span class="flex items-center"
                                  ><span class="mr-1">❤️</span>
                                  {{ user.likes }}</span
                                >
                                <span class="flex items-center"
                                  ><span class="mr-1">🎁</span>
                                  {{ user.gifts }}</span
                                >
                              </div>
                            </div>
                          </div>
                        </li>
                      </TransitionGroup>
                    </div>
                  </div>
                </template>

                <script setup>
                  import { ref, onMounted, onUnmounted, computed } from "vue";

                  const leaderboard = ref([]);
                  let ws = null;

                  // Computed property to filter users with comments > 0 (as per requirement)
                  // But wait, requirement says "Show only users with Comment > 0".
                  // However, backend sends top 5 regardless.
                  // If backend sends top 5, and some have 0 comments, should I hide them?
                  // Or should backend filter?
                  // "รายชื่อที่ปรากฏใน board ให้ปรากฏเฉพาะผู้ที่ Comment > 0"
                  // If I filter here, I might show less than 5.
                  // Ideally backend should send more, or filter there.
                  // For now, I'll filter here.
                  const filteredLeaderboard = computed(() => {
                    return leaderboard.value.filter((u) => u.comments > 0);
                  });

                  const connectWebSocket = () => {
                    ws = new WebSocket("ws://localhost:8000/ws");

                    ws.onmessage = (event) => {
                      const data = JSON.parse(event.data);
                      if (data.leaderboard) {
                        // Transform data to match UI needs
                        leaderboard.value = data.leaderboard.map((item) => {
                          const [id, name] = item.user_key.split("|", 2);
                          return {
                            user_id: id,
                            nickname: name,
                            score: item.score,
                            avatar_url: null, // Backend doesn't send avatar yet in leaderboard list, need to fix or use placeholder
                            comments: 0, // Backend doesn't send breakdown in leaderboard list yet
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
                    transition: all 0.5s ease;
                  }

                  .list-enter-from,
                  .list-leave-to {
                    opacity: 0;
                    transform: translateX(30px);
                  }

                  .list-leave-active {
                    position: absolute;
                  }
                </style>
              </div>
            </div>
          </div>
        </div></TransitionGroup
      >
    </div>
  </div>
</template>
