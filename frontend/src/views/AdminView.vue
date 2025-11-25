<template>
  <div class="min-h-screen bg-gray-100 p-6 flex flex-col gap-6">
    <!-- Top Section: 3 Columns -->
    <div class="grid grid-cols-12 gap-6 h-[500px]">
      <!-- Left: Stream Control (3 cols) -->
      <div class="col-span-3 bg-white rounded-xl shadow-md p-6 flex flex-col">
        <h2 class="text-xl font-bold mb-4 text-gray-800 flex items-center">
          <span class="mr-2">🎮</span> Stream Control
        </h2>

        <!-- Status -->
        <div class="mb-6 p-4 rounded-lg text-center" :class="statusColorClass">
          <p class="text-sm font-semibold uppercase tracking-wider">Status</p>
          <p class="text-2xl font-black">{{ store.connectionStatus }}</p>
        </div>

        <!-- Controls -->
        <div class="space-y-4 flex-1">
          <!-- Start -->
          <div v-if="store.connectionStatus === 'disconnected'">
            <label class="block text-sm font-medium text-gray-700 mb-1"
              >TikTok Username (@)</label
            >
            <input
              v-model="tiktokUsername"
              type="text"
              class="w-full p-2 border rounded-lg mb-2"
              placeholder="username"
            />
            <button
              @click="startStream"
              class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg transition shadow-lg flex items-center justify-center"
              :disabled="store.isLoading"
            >
              <span v-if="store.isLoading" class="animate-spin mr-2">⏳</span>
              Start Stream
            </button>
          </div>

          <!-- Pause/Resume/Stop -->
          <div v-else class="space-y-3">
            <button
              v-if="store.isPaused"
              @click="resumeStream"
              class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 rounded-lg transition shadow"
            >
              ▶ Resume Stream
            </button>
            <button
              v-else
              @click="pauseStream"
              class="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-3 rounded-lg transition shadow"
            >
              ⏸ Pause Stream
            </button>

            <button
              @click="confirmStop"
              class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition shadow"
            >
              ⏹ Stop Stream
            </button>
          </div>

          <hr class="border-gray-200 my-4" />

          <!-- Reset Session -->
          <button
            @click="resetSession"
            class="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 rounded-lg transition"
          >
            🔄 Reset Session
          </button>
        </div>
      </div>

      <!-- Middle: Leaderboard (5 cols) -->
      <div
        class="col-span-5 bg-white rounded-xl shadow-md p-6 flex flex-col overflow-hidden"
      >
        <h2
          class="text-xl font-bold mb-4 text-gray-800 flex items-center justify-between"
        >
          <span>🏆 Live Leaderboard</span>
          <span class="text-sm font-normal text-gray-500"
            >{{ store.leaderboard.length }} users</span
          >
        </h2>

        <div class="flex-1 overflow-y-auto pr-2 space-y-1">
          <div
            v-for="(user, index) in store.leaderboard"
            :key="user.user_key"
            @click="selectUser(user)"
            class="flex items-center p-2 rounded-lg cursor-pointer transition border hover:bg-blue-50 hover:border-blue-300"
            :class="
              selectedUser?.user_id === user.user_id
                ? 'bg-blue-100 border-blue-500'
                : 'bg-gray-50 border-transparent'
            "
          >
            <!-- Rank -->
            <div
              class="w-6 h-6 flex items-center justify-center rounded-full font-bold mr-2 text-xs"
              :class="
                index < 3
                  ? 'bg-yellow-400 text-white'
                  : 'bg-gray-200 text-gray-600'
              "
            >
              {{ index + 1 }}
            </div>

            <!-- Avatar -->
            <img
              :src="
                user.avatar_url ||
                `https://ui-avatars.com/api/?name=${user.nickname}&background=random`
              "
              class="w-8 h-8 rounded-full border border-gray-200 mr-2 object-cover"
            />

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-center">
                <p class="font-bold text-gray-900 truncate text-sm">
                  {{ user.nickname }}
                </p>
                <div class="text-right font-black text-sm text-blue-600">
                  {{ user.score }}
                </div>
              </div>

              <!-- Stats -->
              <div class="flex items-center text-xs text-gray-500 space-x-2 mt-0.5">
                <span>💬 {{ user.comments }}</span>
                <span>❤️ {{ user.likes }}</span>
                <span>🎁 {{ user.gifts }}</span>
              </div>
              
              <!-- Gift Icons Breakdown -->
              <div class="flex items-center gap-1 mt-1 overflow-x-auto">
                <div
                  v-for="(gift, name) in user.gifts_breakdown"
                  :key="name"
                  class="flex items-center bg-gray-100 rounded px-1 py-0.5 text-[10px] whitespace-nowrap"
                  :title="`${name} (ID: ${gift.id}) - ${gift.diamond_count} diamonds`"
                >
                  <img v-if="gift.icon" :src="gift.icon" class="w-3 h-3 mr-1" />
                  <span v-else>🎁</span>
                  <span>x{{ gift.count }}</span>
                  <span class="text-gray-400 ml-0.5"
                    >({{ gift.count * gift.diamond_count }})</span
                  >
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: User Info (4 cols) -->
      <div class="col-span-4 bg-white rounded-xl shadow-md p-6 flex flex-col h-full overflow-hidden">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800">👤 User Details</h2>
          <button
            v-if="selectedUser"
            @click="resetUserScore"
            class="bg-red-100 hover:bg-red-200 text-red-700 font-bold py-2 px-3 rounded-lg transition text-xs flex items-center"
          >
            🗑 Reset Score
          </button>
        </div>

        <div v-if="selectedUser" class="flex-1 flex flex-col overflow-hidden">
          <!-- Profile Header -->
          <div class="flex items-center space-x-4 mb-4 flex-shrink-0">
            <img
              :src="
                selectedUser.avatar_url ||
                `https://ui-avatars.com/api/?name=${selectedUser.nickname}&background=random`
              "
              class="w-16 h-16 rounded-full border-4 border-blue-100 shadow-sm object-cover"
            />
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-gray-900">
                  {{ selectedUser.nickname }}
                </h3>
                <span
                  class="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full font-bold"
                >
                  Score: {{ selectedUser.score }}
                </span>
              </div>
              <p class="text-gray-500 text-xs">
                ID: {{ selectedUser.user_id }}
              </p>
              <!-- Used Stats Summary -->
              <div v-if="selectedUser.used_likes || selectedUser.used_gifts_sent" class="text-[10px] text-gray-400 mt-1">
                History: {{ selectedUser.used_likes || 0 }} Likes, {{ selectedUser.used_gifts_sent || 0 }} Gifts
              </div>
            </div>
          </div>

          <!-- Gift Breakdown (Horizontal Scroll) - Reduced Size -->
          <div
            v-if="giftBreakdown && Object.keys(giftBreakdown).length > 0"
            class="mb-4 bg-yellow-50 p-2 rounded-lg border border-yellow-200 flex-shrink-0"
          >
            <h4 class="font-bold text-yellow-800 mb-1 text-[10px]">
              🎁 Gifts
            </h4>
            <div class="flex overflow-x-auto space-x-2 pb-1">
              <div
                v-for="(gift, name) in giftBreakdown"
                :key="name"
                class="flex flex-col items-center bg-white p-1 rounded shadow-sm min-w-[40px] cursor-help border border-yellow-100"
                :title="`${name} (ID: ${gift.id}) - ${gift.diamond_count} diamonds`"
              >
                <img v-if="gift.icon" :src="gift.icon" class="w-6 h-6 mb-0.5 object-contain" />
                <span v-else class="text-xs mb-0.5">🎁</span>
                <span class="font-bold text-[10px] text-gray-800">x{{ gift.count }}</span>
              </div>
            </div>
          </div>

          <!-- Comments Section -->
          <div class="flex-1 overflow-hidden flex flex-col min-h-0">
            
            <!-- Unused Comments (Expanded by default) -->
            <div class="flex flex-col flex-1 overflow-hidden mb-2">
                <div 
                    @click="isUnusedCommentsOpen = !isUnusedCommentsOpen"
                    class="flex items-center justify-between cursor-pointer bg-gray-100 p-2 rounded-t-lg hover:bg-gray-200 transition"
                >
                    <h4 class="font-bold text-gray-700 flex items-center text-sm">
                        <span>💬 Unused Comments</span>
                        <span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">{{ unusedComments.length }}</span>
                    </h4>
                    <span class="text-xs text-gray-500">{{ isUnusedCommentsOpen ? '▼' : '▶' }}</span>
                </div>
                
                <div v-if="isUnusedCommentsOpen" class="flex-1 overflow-y-auto bg-gray-50 border border-t-0 border-gray-200 rounded-b-lg p-2 space-y-2">
                    <div
                        v-for="(comment, idx) in unusedComments"
                        :key="idx"
                        class="bg-white p-2 rounded border border-gray-200 hover:border-blue-300 transition flex justify-between items-start gap-2"
                    >
                        <div class="flex-1 min-w-0">
                            <div class="text-[10px] text-gray-400 mb-0.5">{{ new Date(comment.timestamp).toLocaleTimeString() }}</div>
                            <p class="text-sm text-gray-800 break-words">"{{ comment.content }}"</p>
                        </div>
                        <button
                            @click="selectQuestion(comment.content)"
                            class="text-blue-500 hover:text-blue-700 hover:bg-blue-50 p-2.0 rounded transition"
                            title="Share to Screen"
                        >
                            🛜
                        </button>
                    </div>
                    <div v-if="unusedComments.length === 0" class="text-center text-gray-400 py-4 text-xs italic">
                        No unused comments.
                    </div>
                </div>
            </div>

            <!-- Used Comments (Collapsed by default) -->
            <div class="flex flex-col flex-shrink-0">
                <div 
                    @click="isUsedCommentsOpen = !isUsedCommentsOpen"
                    class="flex items-center justify-between cursor-pointer bg-gray-100 p-2 rounded-t-lg hover:bg-gray-200 transition"
                >
                    <h4 class="font-bold text-gray-600 flex items-center text-sm">
                        <span>history Used Comments</span>
                        <span class="ml-2 text-xs bg-gray-200 px-2 py-0.5 rounded-full">{{ usedComments.length }}</span>
                    </h4>
                    <span class="text-xs text-gray-500">{{ isUsedCommentsOpen ? '▼' : '▶' }}</span>
                </div>
                
                <div v-if="isUsedCommentsOpen" class="max-h-40 overflow-y-auto bg-gray-50 border border-t-0 border-gray-200 rounded-b-lg p-2 space-y-2">
                     <div
                        v-for="(comment, idx) in usedComments"
                        :key="idx"
                        class="bg-gray-100 p-2 rounded border border-gray-200 flex justify-between items-start gap-2 opacity-75"
                    >
                        <div class="flex-1 min-w-0">
                            <div class="text-[10px] text-gray-400 mb-0.5">{{ new Date(comment.timestamp).toLocaleTimeString() }}</div>
                            <p class="text-sm text-gray-600 break-words">"{{ comment.content }}"</p>
                        </div>
                        <!-- Re-use button? Optional. -->
                         <button
                            @click="selectQuestion(comment.content)"
                            class="text-gray-400 hover:text-blue-500 hover:bg-gray-200 p-1.5 rounded transition"
                            title="Re-share"
                        >
                            🔄
                        </button>
                    </div>
                    <div v-if="usedComments.length === 0" class="text-center text-gray-400 py-4 text-xs italic">
                        No used comments history.
                    </div>
                </div>
            </div>

          </div>
        </div>

        <div
          v-else
          class="flex-1 flex items-center justify-center text-gray-400 italic"
        >
          Select a user from the leaderboard to view details.
        </div>
      </div>
    </div>

    <!-- Bottom Section: Logs -->
    <div
      class="bg-white rounded-xl shadow-md p-4 flex-1 h-[250px] min-h-[150px] max-h-[150px] flex flex-col"
    >
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-bold text-gray-800">📜 System Logs</h2>
        <!-- Tabs -->
        <div class="flex space-x-1">
          <button
            v-for="tab in logTabs"
            :key="tab"
            @click="activeTab = tab"
            class="px-3 py-1 rounded text-xs font-bold transition"
            :class="
              activeTab === tab
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            "
          >
            {{ tab }}
          </button>
        </div>
      </div>

      <div
        class="flex-1 bg-gray-900 rounded-lg p-2 overflow-y-auto font-mono text-xs"
      >
        <div v-for="(log, index) in filteredLogs" :key="index" class="mb-0.5">
          <span class="text-gray-500">[{{ log.time }}]</span>
          <span :class="getLogColor(log.type)" class="font-bold mx-2"
            >[{{ log.type }}]</span
          >
          <span class="text-gray-300">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useGameStore } from "../stores/gameStore";
import axios from "axios";

const store = useGameStore();
const tiktokUsername = ref("");
const selectedUser = ref(null);
const userComments = ref([]);
const giftBreakdown = ref({});
const activeTab = ref("All");
const logTabs = ["All", "System", "Chat", "Gift", "Like"]; // Removed "System"

// UI State for Collapsible Sections
const isUnusedCommentsOpen = ref(true);
const isUsedCommentsOpen = ref(false);

// Computed
const statusColorClass = computed(() => {
  switch (store.connectionStatus) {
    case "connected":
      return "bg-green-100 text-green-800";
    case "disconnected":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
});

const filteredLogs = computed(() => {
  if (activeTab.value === "All") {
    return store.logs;
  }
  
  return store.logs.filter((log) => log.type === activeTab.value);
});

const unusedComments = computed(() => {
    return userComments.value.filter(c => !c.is_used);
});

const usedComments = computed(() => {
    return userComments.value.filter(c => c.is_used);
});

// Methods
const startStream = () => {
  if (!tiktokUsername.value) return alert("Please enter a username");
  store.startStream(tiktokUsername.value);
};

const pauseStream = () => store.pauseStream();
const resumeStream = () => store.resumeStream();
const resetSession = () => {
  if (
    confirm(
      "Are you sure you want to reset the session? This will clear all data."
    )
  ) {
    store.resetSession();
  }
};
const confirmStop = () => {
  if (confirm("Are you sure you want to STOP the stream?")) {
    store.stopStream();
  }
};

const selectUser = async (user) => {
  selectedUser.value = user;
  // Fetch detailed info including comments
  try {
    const response = await axios.get(
      `http://localhost:8000/user/${user.user_id}`
    );
    // Assuming response.data contains { stats: {}, comments: [], gifts_breakdown: {} }
    userComments.value = response.data.comments || [];
    giftBreakdown.value = response.data.gifts_breakdown || {};
    // Update selectedUser with more details if needed
    selectedUser.value = { ...user, ...response.data.stats };
    
    // Reset collapsible state when selecting new user
    isUnusedCommentsOpen.value = true;
    isUsedCommentsOpen.value = false;
  } catch (error) {
    console.error("Failed to fetch user details", error);
  }
};

const selectQuestion = async (commentText) => {
  if (!selectedUser.value) return;
  try {
    await axios.post("http://localhost:8000/question", {
      user_id: selectedUser.value.user_id,
      nickname: selectedUser.value.nickname,
      avatar_url: selectedUser.value.avatar_url,
      content: commentText,
    });
    alert("Question selected for overlay!");
    
    // Optimistically mark as used in UI or re-fetch
    // For now, let's re-fetch to be safe and sync with DB
    await selectUser(selectedUser.value);
    
  } catch (error) {
    console.error("Failed to set question", error);
  }
};

const resetUserScore = async () => {
  if (!selectedUser.value) return;
  if (confirm(`Reset score for ${selectedUser.value.nickname}?`)) {
    try {
      await axios.post(
        `http://localhost:8000/user/${selectedUser.value.user_id}/reset`
      );
      // Refresh leaderboard
      // store.fetchLeaderboard(); // WebSocket handles this
      alert("User score reset.");
      // Refresh user details
      await selectUser(selectedUser.value);
    } catch (error) {
      console.error("Failed to reset user score", error);
    }
  }
};

const getLogColor = (type) => {
  switch (type) {
    case "System":
      return "text-blue-400";
    case "Chat":
      return "text-green-400";
    case "Gift":
      return "text-yellow-400";
    case "Like":
      return "text-pink-400";
    default:
      return "text-gray-400";
  }
};

onMounted(() => {
  store.connectWebSocket();
});
</script>
