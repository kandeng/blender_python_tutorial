// Chat state (messages, input)

import { ref } from 'vue'

export function useChatStore() {
  // Reactive state
  const chatMessages = ref([
    // Initial welcome message
    {
      id: 1,
      content: 'Hello! How can I help you today?',
      sender: 'ai',
      avatar: '/src/assets/icons/robot.svg',
      files: []
    }
  ])
  const messageInput = ref('')
  const uploadFiles = ref([])
  const aiAvatar = ref('/src/assets/icons/robot.svg')
  const userAvatar = ref('/src/assets/icons/user.svg')

  // Handle file upload/removal
  const handleFileUpload = (file, removeIndex) => {
    // Case 1: Remove file
    if (file === null && removeIndex !== undefined) {
      uploadFiles.value.splice(removeIndex, 1)
      console.log('File removed at index:', removeIndex, 'Current files:', uploadFiles.value)
      return
    }

    // Case 2: Guard against invalid files
    if (!file || !file.name || !file.size) {
      console.warn('Invalid file object received:', file)
      return
    }

    // Case 3: Add valid file
    uploadFiles.value.push(file)
    console.log('File added successfully:', file.name, 'Total files:', uploadFiles.value.length)
  }

  // Send message (with files)
  const sendMessage = (message) => {
    // Validate: empty message + no files = do nothing
    if (!message.trim() && uploadFiles.value.length === 0) return

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      content: message,
      sender: 'user',
      avatar: userAvatar.value,
      files: [...uploadFiles.value] // Attach selected files
    }
    chatMessages.value.push(userMessage)

    // Clear input and files after sending
    messageInput.value = ''
    uploadFiles.value = []

    // Simulate AI response (replace with real API call)
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        content: `I received your message: "${message || '(file only)'}"! How can I assist further?`,
        sender: 'ai',
        avatar: aiAvatar.value,
        files: []
      }
      chatMessages.value.push(aiResponse)
    }, 1000)
  }

  // Reset chat (optional)
  const resetChat = () => {
    chatMessages.value = [
      {
        id: Date.now(),
        content: 'Hello! How can I help you today?',
        sender: 'ai',
        avatar: '@/assets/ai-avatar.png',
        files: []
      }
    ]
    messageInput.value = ''
    uploadFiles.value = []
  }

  // Return reactive state and methods
  return {
    chatMessages,
    messageInput,
    uploadFiles,
    aiAvatar,
    userAvatar,
    handleFileUpload,
    sendMessage,
    resetChat
  }
}