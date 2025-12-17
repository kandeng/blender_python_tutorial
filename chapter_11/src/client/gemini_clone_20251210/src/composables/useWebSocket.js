// WebSocket + server communication
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export const useWebSocket = (chatMessages, uploadFiles) => {
  const SERVER_URL = 'http://localhost:8000'
  const WS_URL = `ws://localhost:8000/ws/`
  const userId = ref('user_' + Math.random().toString(36).slice(2, 11))
  let ws = null

  // Initialize WebSocket
  const initWebSocket = () => {
    if (ws) ws.close()
    ws = new WebSocket(`${WS_URL}${userId.value}`)

    ws.onopen = async () => {
      console.log('WebSocket connected to FastAPI server')
      ElMessage.success('Connected to chat server!')
      // Fetch chat history from server
      try {
        const res = await axios.get(`${SERVER_URL}/history/${userId.value}`)
        chatMessages.value = res.data.history
      } catch (e) {
        console.error('Failed to fetch history:', e)
      }
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      // Enforce sender for AI messages
      if (!msg.sender) {
        msg.sender = 'ai'; 
      }
      // Add AI avatar if missing
      if (msg.sender === 'ai' && !msg.avatar) {
        msg.avatar = '/src/assets/icons/robot.svg';
      }

      // Deduplicate and add to chat
      const isDuplicate = chatMessages.value.some(
        m => m.timestamp === msg.timestamp && m.content === msg.content
      )
      if (!isDuplicate) {
        chatMessages.value.push(msg)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      ElMessage.error('Failed to connect to chat server (falling back to HTTP)')
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setTimeout(initWebSocket, 3000)
    }
  }

  // Send message via WebSocket (fallback to HTTP)
  const sendMessage = (content) => {
    if (!content.trim() && uploadFiles.value.length === 0) return

    const userMsg = {
      sender: 'user',  // Explicitly set sender
      content: content.trim(),
      files: [...uploadFiles.value],
      timestamp: new Date().toISOString(),
      avatar: '/src/assets/icons/user.svg' 
    }
    chatMessages.value.push(userMsg)    

    // Send to server
    if (ws && ws.readyState === WebSocket.OPEN) {
      sendMessageViaWS(content, uploadFiles.value)
    } else {
      sendMessageViaHTTP(content, uploadFiles.value)
    }

    // Clear input/files
    uploadFiles.value = []
    return '' // Reset input
  }

  // Send via WebSocket
  const sendMessageViaWS = (content, files) => {
    const fileMetadata = files.map(file => ({
      name: file.name,
      type: file.type,
      size: file.size
    }))
    ws.send(JSON.stringify({ content, files: fileMetadata }))
  }

  // Send via HTTP
  const sendMessageViaHTTP = async (content, files) => {
    try {
      const formData = new FormData()
      formData.append('user_id', userId.value)
      formData.append('content', content)
      files.forEach(file => formData.append('files', file))

      const response = await axios.post(`${SERVER_URL}/receive/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      chatMessages.value.push(response.data.ai_message)
    } catch (error) {
      console.error('HTTP send error:', error)
      ElMessage.error('Failed to send message to server')
    }
  }

  // Cleanup WebSocket
  onUnmounted(() => {
    if (ws) ws.close()
  })

  // Initialize on mount
  initWebSocket()

  return {
    sendMessage,
    userId
  }
}