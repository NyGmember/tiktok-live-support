import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGameStore = defineStore('game', () => {
    const isConnected = ref(false)
    const leaderboard = ref([])
    const status = ref({})

    function connect() {
        // TODO: Implement WebSocket connection
        console.log('Connecting to WebSocket...')
    }

    return { isConnected, leaderboard, status, connect }
})
