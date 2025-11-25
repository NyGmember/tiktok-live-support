<template>
  <div class="min-h-screen bg-gray-100 p-6 flex flex-col gap-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <router-link
            to="/"
            class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg transition"
        >
            🔙 Back to Admin
        </router-link>
        <h1 class="text-3xl font-bold text-gray-800">📊 Session Dashboard</h1>
      </div>
    </div>

    <!-- Top Section: Session List -->
    <div class="bg-white rounded-xl shadow-md p-6">
      <h2 class="text-xl font-bold mb-4 text-gray-800">📜 All Sessions History</h2>
      <div class="overflow-x-auto">
        <div class="max-h-[200px] overflow-y-auto border rounded-lg">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50 sticky top-0">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Channel</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Score</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr 
                v-for="session in allSessions" 
                :key="session.id" 
                @click="selectSession(session)"
                class="hover:bg-blue-50 cursor-pointer transition"
                :class="selectedSession?.id === session.id ? 'bg-blue-100' : ''"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{{ session.channel_name || 'Unknown' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(session.start_time).toLocaleString() }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ session.end_time ? new Date(session.end_time).toLocaleString() : '-' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span :class="session.status === 'STREAMING' ? 'text-green-600 font-bold' : 'text-gray-500'">
                        {{ session.status }}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-blue-600">{{ session.total_score || 0 }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button class="text-blue-600 hover:text-blue-800 font-bold">View</button>
                </td>
              </tr>
              <tr v-if="allSessions.length === 0">
                <td colspan="6" class="px-6 py-4 text-center text-gray-500 italic">No sessions found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Bottom Section: Session Details & Visualization -->
    <div v-if="selectedSession" class="grid grid-cols-12 gap-6 flex-1">
        <!-- Stats Summary -->
        <div class="col-span-4 bg-white rounded-xl shadow-md p-6">
            <h3 class="text-lg font-bold mb-4 text-gray-800 border-b pb-2">📈 Session Stats: {{ selectedSession.channel_name }}</h3>
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Session ID:</span>
                    <span class="font-mono text-xs text-gray-500 truncate w-32" :title="selectedSession.id">{{ selectedSession.id }}</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Status:</span>
                    <span class="font-bold" :class="selectedSession.status === 'STREAMING' ? 'text-green-600' : 'text-gray-600'">{{ selectedSession.status }}</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Total Users:</span>
                    <span class="font-bold text-gray-900">{{ sessionDetails.leaderboard?.length || 0 }}</span>
                </div>
                <!-- Add more aggregate stats here if available -->
            </div>
        </div>

        <!-- Visualization (Top Users Bar Chart) -->
        <div class="col-span-8 bg-white rounded-xl shadow-md p-6 flex flex-col">
            <h3 class="text-lg font-bold mb-4 text-gray-800">🏆 Top Performers</h3>
            <div class="flex-1 flex items-end justify-around gap-2 h-[300px] border-b border-l p-4 bg-gray-50 relative">
                <div 
                    v-for="(user, index) in topUsers" 
                    :key="user.user_id"
                    class="flex flex-col items-center justify-end w-16 group relative"
                    :style="{ height: `${(user.score / maxScore) * 100}%` }"
                >
                    <!-- Bar -->
                    <div 
                        class="w-full bg-blue-500 rounded-t-md hover:bg-blue-600 transition-all relative"
                        :class="index === 0 ? 'bg-yellow-500' : (index === 1 ? 'bg-gray-400' : (index === 2 ? 'bg-orange-400' : ''))"
                        style="height: 100%; min-height: 4px;"
                    >
                         <!-- Tooltip -->
                        <div class="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-10 pointer-events-none">
                            {{ user.nickname }}: {{ user.score }}
                        </div>
                    </div>
                    
                    <!-- Label -->
                    <div class="mt-2 text-xs text-gray-600 truncate w-full text-center font-bold" :title="user.nickname">
                        {{ user.nickname }}
                    </div>
                    <div class="text-[10px] text-gray-400">
                        {{ user.score }}
                    </div>
                </div>
                 <div v-if="topUsers.length === 0" class="absolute inset-0 flex items-center justify-center text-gray-400 italic">
                    No data to display.
                </div>
            </div>
        </div>
    </div>
    
    <div v-else class="flex-1 flex items-center justify-center text-gray-400 italic bg-white rounded-xl shadow-md p-10">
        Select a session to view details.
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const allSessions = ref([]);
const selectedSession = ref(null);
const sessionDetails = ref({});

const fetchSessions = async () => {
    try {
        const res = await axios.get("http://localhost:8000/sessions/history");
        // Show all sessions (no filter)
        allSessions.value = res.data;
        
        // Select most recent by default
        if (allSessions.value.length > 0) {
            selectSession(allSessions.value[0]);
        }
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
};

const selectSession = async (session) => {
    selectedSession.value = session;
    try {
        const res = await axios.get(`http://localhost:8000/sessions/${session.id}`);
        sessionDetails.value = res.data;
    } catch (e) {
        console.error("Failed to fetch session details", e);
    }
};

const topUsers = computed(() => {
    if (!sessionDetails.value.leaderboard) return [];
    return sessionDetails.value.leaderboard.slice(0, 10); // Top 10
});

const maxScore = computed(() => {
    if (topUsers.value.length === 0) return 100;
    return Math.max(...topUsers.value.map(u => u.score));
});

onMounted(() => {
    fetchSessions();
});
</script>
