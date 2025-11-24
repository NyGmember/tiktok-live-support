<template>
  <div
    class="w-screen h-screen bg-[#00FF00] flex items-center justify-center overflow-hidden"
  >
    <transition name="pop">
      <div v-if="question" class="relative max-w-2xl w-full p-8">
        <!-- Speech Bubble Frame -->
        <div
          class="bg-white rounded-3xl shadow-2xl border-4 border-blue-500 p-6 relative"
        >
          <!-- Triangle for speech bubble -->
          <div
            class="absolute -bottom-4 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[20px] border-l-transparent border-r-[20px] border-r-transparent border-t-[20px] border-t-blue-500"
          ></div>

          <div class="flex items-start space-x-6">
            <!-- User Avatar -->
            <div class="flex-shrink-0">
              <img
                :src="question.avatar_url"
                class="w-24 h-24 rounded-full border-4 border-yellow-400 shadow-lg"
                alt="User Avatar"
              />
            </div>

            <!-- Content -->
            <div class="flex-1">
              <h2 class="text-2xl font-bold text-blue-600 mb-2">
                {{ question.nickname }}
              </h2>
              <p class="text-3xl font-black text-gray-800 leading-tight">
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
