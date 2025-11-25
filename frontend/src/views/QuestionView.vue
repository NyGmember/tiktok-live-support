<template>
  <div
    class="w-screen h-screen bg-[#00FF00] flex items-start justify-end overflow-hidden p-10"
  >
    <transition name="pop">
      <div v-if="question" class="relative max-w-sm w-full">
        <!-- Speech Bubble Frame -->
        <div
          class="bg-white rounded-2xl shadow-xl border-4 border-blue-500 p-4 relative"
        >
          <!-- Triangle for speech bubble (Adjusted for smaller size) -->
          <div
            class="absolute -bottom-3 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[10px] border-l-transparent border-r-[10px] border-r-transparent border-t-[10px] border-t-blue-500"
          ></div>

          <div class="flex items-start space-x-3">
            <!-- User Avatar -->
            <div class="flex-shrink-0">
              <img
                :src="question.avatar_url"
                class="w-12 h-12 rounded-full border-2 border-yellow-400 shadow-md"
                alt="User Avatar"
              />
            </div>

            <!-- Content -->
            <div class="flex-1">
              <h2 class="text-sm font-bold text-blue-600 mb-1">
                {{ question.nickname }}
              </h2>
              <p class="text-lg font-black text-gray-800 leading-tight">
                "{{ question.content }}"
              </p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const question = ref(null);
let ws = null;

const connectWebSocket = () => {
  ws = new WebSocket("ws://localhost:8000/ws");

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.question) {
      question.value = data.question;
    } else {
      question.value = null;
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
.pop-enter-active,
.pop-leave-active {
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.5) translateY(50px);
}
</style>
