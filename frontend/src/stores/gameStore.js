import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
    // State
    const isConnected = ref(false)
    const isScoringActive = ref(false)
    const currentSessionId = ref('')
    const targetTiktokId = ref('')
    const leaderboard = ref([])
    const logs = ref([])
    const ws = ref(null)

    // Actions
    async function fetchStatus() {
        try {
            const res = await fetch('http://localhost:8000/status')
            const data = await res.json()
            isConnected.value = data.is_connected
            isScoringActive.value = data.is_scoring_active
            currentSessionId.value = data.current_session_id
            targetTiktokId.value = data.target_tiktok_id
        } catch (e) {
            console.error('Failed to fetch status:', e)
            addLog('ERROR', `Failed to fetch status: ${e.message}`)
        }
    }

    function connectWebSocket() {
        if (ws.value) return

        ws.value = new WebSocket('ws://localhost:8000/ws/leaderboard')

        ws.value.onopen = () => {
            addLog('INFO', 'WebSocket connected')
        }

        ws.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                leaderboard.value = data
            } catch (e) {
                console.error('WS Parse Error:', e)
            }
        }

        ws.value.onclose = () => {
            addLog('WARNING', 'WebSocket disconnected. Reconnecting...')
            ws.value = null
            setTimeout(connectWebSocket, 3000)
        }

        ws.value.onerror = (error) => {
            console.error('WebSocket error:', error)
        }
    }

    async function startStream(targetId, mode) {
        try {
            const res = await fetch(`http://localhost:8000/control/start?target_id=${targetId}&mode=${mode}`, {
                method: 'POST'
            })
            const data = await res.json()
            if (data.status === 'started') {
                isConnected.value = true
                addLog('INFO', `Stream started for ${targetId} (${mode})`)
            }
        } catch (e) {
            addLog('ERROR', `Failed to start stream: ${e.message}`)
        }
    }

    async function stopStream() {
        try {
            const res = await fetch('http://localhost:8000/control/stop', {
                method: 'POST'
            })
            const data = await res.json()
            if (data.status === 'stopped') {
                isConnected.value = false
                addLog('INFO', 'Stream stopped')
            }
        } catch (e) {
            addLog('ERROR', `Failed to stop stream: ${e.message}`)
        }
    }

    async function resetSession(sessionId) {
        try {
            const res = await fetch('http://localhost:8000/session/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, reset_scores: true })
            })
            const data = await res.json()
            currentSessionId.value = data.session_id
            leaderboard.value = []
            addLog('INFO', `Session reset: ${sessionId}`)
        } catch (e) {
            addLog('ERROR', `Failed to reset session: ${e.message}`)
        }
    }

    async function selectWinner() {
        try {
            const res = await fetch('http://localhost:8000/winner/select', {
                method: 'POST'
            })
            if (!res.ok) throw new Error('No winner found')
            const data = await res.json()
            addLog('INFO', `Winner selected: ${data.nickname}`)
            return data
        } catch (e) {
            addLog('ERROR', `Failed to select winner: ${e.message}`)
            return null
        }
    }

    function addLog(level, message) {
        logs.value.unshift({
            timestamp: new Date().toISOString(),
            level,
            message
        })
        // Keep only last 100 logs
        if (logs.value.length > 100) {
            logs.value.pop()
        }
    }

    return {
        isConnected,
        isScoringActive,
        currentSessionId,
        targetTiktokId,
        leaderboard,
        logs,
        fetchStatus,
        connectWebSocket,
        startStream,
        stopStream,
        resetSession,
        selectWinner,
        addLog
    }
})
