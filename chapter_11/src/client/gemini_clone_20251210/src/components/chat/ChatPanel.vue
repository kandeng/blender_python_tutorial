<!-- src/components/chat/ChatPanel.vue -->
<template>
  <div class="chat-panel">
    <!-- Chat messages panel -->
    <div class="chat-messages-container">
      <div class="chat-messages-inner">
        <div 
          v-for="msg in chatMessages" 
          :key="msg.id"
          :id="`message-${msg.id}`"
          class="message-item"
          :class="{ 'user-message': msg.sender === 'user', 'ai-message': msg.sender === 'ai' }"
        >
          <!-- Avatar -->
          <div class="message-avatar-wrapper">
            <img 
              :src="getAvatarUrl(msg.avatar)" 
              alt="Avatar" 
              class="message-avatar"
              :class="{ 'user-avatar': msg.sender === 'user', 'ai-avatar': msg.sender === 'ai' }"
              @error="handleAvatarError($event, msg.sender)"
            />
          </div>

          <!-- Message content -->
          <div class="message-content-wrapper">
            <div class="message-content">{{ msg.content }}</div>

            <!-- Attached files -->
            <div v-if="msg.files.length" class="message-files">
              <div 
                class="attached-file" 
                v-for="(file, index) in msg.files" 
                :key="index"
              >
                <img src="@/assets/icons/file.svg" alt="File" class="file-icon" />
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">({{ formatFileSize(file.size) }})</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat input component -->
    <ChatInput
      v-model:message-input="messageInput"
      :upload-files="uploadFiles"
      :messages="chatMessages"
      @upload-file="handleFileUpload"
      @send-message="sendMessage"
      @scroll-to-message="scrollToMessage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatInput from './ChatInput.vue'
import { useChatStore } from '@/composables/useChatStore'
import userSvg from '@/assets/icons/user.svg'
import robotSvg from '@/assets/icons/robot.svg'

// Props for chat panel
const props = defineProps({
  active: {
    type: Boolean,
    default: false
  }
})

// Resolve avatar URL
const getAvatarUrl = (avatarPath) => {
  if (!avatarPath) return null
  if (avatarPath.includes('user.svg')) return userSvg
  if (avatarPath.includes('robot.svg')) return robotSvg
  if (avatarPath.startsWith('http')) return avatarPath
  return robotSvg
}

// Get store state and methods
const {
  chatMessages,
  messageInput,
  uploadFiles,
  handleFileUpload: storeHandleFileUpload,
  sendMessage
} = useChatStore()

// Forward file upload/removal to store
const handleFileUpload = (file, removeIndex) => {
  storeHandleFileUpload(file, removeIndex)
}

// Scroll to specific message
const scrollToMessage = (messageId) => {
  const messageElement = document.getElementById(`message-${messageId}`)
  if (messageElement) {
    messageElement.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'center' 
    })
    messageElement.classList.add('highlighted')
    setTimeout(() => {
      messageElement.classList.remove('highlighted')
    }, 2000)
  }
}

// File size formatter
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Auto-scroll to bottom on new messages
onMounted(() => {
  const observer = new MutationObserver(() => {
    const container = document.querySelector('.chat-messages-container')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })

  observer.observe(document.querySelector('.chat-messages-inner'), {
    childList: true,
    subtree: true
  })

  return () => observer.disconnect()
})
</script>

<style scoped>
/* All styles remain the same */
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.chat-messages-container {
  flex: 1;
  padding: 20px 3%;
  overflow-y: auto;
  background-color: #fafafa;
  box-sizing: border-box;
}

.chat-messages-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 80%;
  animation: fadeIn 0.3s ease;
}

.user-message {
  flex-direction: row-reverse;
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.highlighted {
  background-color: #fff3cd;
  border-radius: 8px;
  padding: 4px;
}

.message-avatar-wrapper {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.message-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user-message .message-content {
  background-color: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-content {
  background-color: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

.message-files {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.attached-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  font-size: 14px;
}

.file-icon {
  width: 16px;
  height: 16px;
}

.file-name {
  color: #333;
}

.file-size {
  font-size: 12px;
  color: #666;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-messages-container::-webkit-scrollbar {
  width: 6px;
}

.chat-messages-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-messages-container::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.chat-messages-container::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>