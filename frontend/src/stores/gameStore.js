import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGameStore = defineStore('game', () => {
    // State
    const connectionStatus = ref('disconnected') // 'connected', 'disconnected'
    const isPaused = ref(false)
    const currentSessionId = ref('')
    const targetTiktokId = ref('')
    const leaderboard = ref([])
    const currentQuestion = ref(null)
    const logs = ref([])
    const ws = ref(null)
    const isLoading = ref(false)

    // Actions
    async function fetchStatus() {
        try {
            const res = await fetch('http://localhost:8000/status')
            const data = await res.json()
            connectionStatus.value = data.is_connected ? 'connected' : 'disconnected'
            isPaused.value = data.is_paused
            currentSessionId.value = data.session_id
            targetTiktokId.value = data.target_id
        } catch (e) {
            console.error('Failed to fetch status:', e)
            addLog('ERROR', `Failed to fetch status: ${e.message}`)
        }
    }

    function connectWebSocket() {
        if (ws.value) return

        ws.value = new WebSocket('ws://localhost:8000/ws')

        ws.value.onopen = () => {
            addLog('INFO', 'WebSocket connected')
        }

        ws.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.leaderboard) leaderboard.value = data.leaderboard
                if (data.question !== undefined) currentQuestion.value = data.question
                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(log => {
                        addLog(log.level, log.message, log.type)
                    })
                }
                if (data.status) {
                    connectionStatus.value = data.status.is_connected ? 'connected' : 'disconnected'
                    isPaused.value = data.status.is_paused
                    currentSessionId.value = data.status.session_id
                }
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

    async function startStream(username, mode = 'live') {
        isLoading.value = true
        try {
            const res = await fetch('http://localhost:8000/stream/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tiktok_username: username, mode })
            })
            const data = await res.json()
            if (data.status === 'started') {
                connectionStatus.value = 'connected'
                addLog('INFO', `Stream started for ${username} (${mode})`)
            }
        } catch (e) {
            addLog('ERROR', `Failed to start stream: ${e.message}`)
        } finally {
            isLoading.value = false
        }
    }

    async function stopStream() {
        try {
            const res = await fetch('http://localhost:8000/stream/stop', {
                method: 'POST'
            })
            const data = await res.json()
            if (data.status === 'stopped') {
                connectionStatus.value = 'disconnected'
                addLog('INFO', 'Stream stopped')
            }
        } catch (e) {
            addLog('ERROR', `Failed to stop stream: ${e.message}`)
        }
    }

    async function pauseStream() {
        try {
            await fetch('http://localhost:8000/stream/pause', { method: 'POST' })
            isPaused.value = true
            addLog('INFO', 'Stream paused')
        } catch (e) {
            addLog('ERROR', `Failed to pause stream: ${e.message}`)
        }
    }

    async function resumeStream() {
        try {
            await fetch('http://localhost:8000/stream/resume', { method: 'POST' })
            isPaused.value = false
            addLog('INFO', 'Stream resumed')
        } catch (e) {
            addLog('ERROR', `Failed to resume stream: ${e.message}`)
        }
    }

    async function setSession(sessionId, resetScores = false) {
        try {
            const res = await fetch('http://localhost:8000/session/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, reset_scores: resetScores })
            })
            const data = await res.json()
            currentSessionId.value = data.session_id
            addLog('INFO', `Session set: ${data.session_id}`)
        } catch (e) {
            addLog('ERROR', `Failed to set session: ${e.message}`)
        }
    }

    async function resetSession() {
        try {
            const newSessionId = `session_${Date.now()}`
            await setSession(newSessionId, true)
        } catch (e) {
            addLog('ERROR', `Failed to reset session: ${e.message}`)
        }
    }

    function addLog(level, message, type = 'System') {
        logs.value.unshift({
            time: new Date().toLocaleTimeString(),
            level,
            type,
            message
        })
    }

    return {
        connectionStatus,
        isPaused,
        currentSessionId,
        targetTiktokId,
        leaderboard,
        currentQuestion,
        logs,
        isLoading,
        fetchStatus,
        connectWebSocket,
        startStream,
        stopStream,
        pauseStream,
        resumeStream,
        resetSession,
        setSession,
        addLog
    }
})
