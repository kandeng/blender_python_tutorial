// Chat state (messages, input)

import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

export const useChatStore = () => {
  const chatMessages = ref([])
  const messageInput = ref('')
  const uploadFiles = ref([])
  const aiAvatar = ref('https://cube.elemecdn.com/6/94/4d3ea53c084bad6931a56d55811281jpeg.jpeg')

  // ✅ Remove messagesContainer (now handled locally in ChatMessages.vue)
  // const messagesContainer = ref(null)

  // Handle file upload (validation)
  const handleFileUpload = (file) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'audio/mpeg', 'video/mp4', 'application/pdf']
    if (!allowedTypes.includes(file.raw.type)) {
      ElMessage.error(`Invalid file type: ${file.raw.type}. Allowed: JPG/PNG/MP3/MP4/PDF`)
      return
    }
    uploadFiles.value.push(file.raw)
  }

  return {
    chatMessages,
    messageInput,
    uploadFiles,
    aiAvatar,
    handleFileUpload
    // ✅ Remove messagesContainer from return
  }
}