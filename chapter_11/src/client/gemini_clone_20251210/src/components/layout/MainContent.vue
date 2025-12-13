<!-- Wrapper for tab content -->
<template>
  <div class="main-content">
    <!-- Chat messages panel (WITH 10% left/right padding) -->
    <div class="chat-messages-container">
      <!-- Wrapper for 90% width content -->
      <div class="chat-messages-inner">
        <div 
          v-for="msg in chatMessages" 
          :key="msg.id"
          :id="`message-${msg.id}`"
          class="message-item"
          :class="{ 'user-message': msg.sender === 'user', 'ai-message': msg.sender === 'ai' }"
        >
          <!-- Avatar (FIXED: use resolved path from script) -->
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
import ChatInput from '../chat/ChatInput.vue'
import { useChatStore } from '@/composables/useChatStore'


// Import local SVGs directly (Vite-compatible)
import userSvg from '@/assets/icons/user.svg'
import robotSvg from '@/assets/icons/robot.svg'

// Resolve avatar URL (optimized for local SVGs)
const getAvatarUrl = (avatarPath) => {
  // If path is empty, return the correct SVG based on sender (handled in error fallback)
  if (!avatarPath) return null

  // Resolve local SVG paths (Vite alias: @ = src/)
  if (avatarPath.includes('user.svg')) return userSvg
  if (avatarPath.includes('robot.svg')) return robotSvg

  // For remote URLs (if needed)
  if (avatarPath.startsWith('http')) return avatarPath

  // Default to robot.svg for AI if path is invalid
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
    // Highlight the message temporarily
    messageElement.classList.add('highlighted')
    setTimeout(() => {
      messageElement.classList.remove('highlighted')
    }, 2000)
  }
}

// File size formatter (consistent with ChatInput)
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
/* Main content container */
.main-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

/* Messages container (100% width with 10% left/right padding) */
.chat-messages-container {
  flex: 1;
  padding: 20px 3%; /* 3% left/right padding + 20px vertical */
  overflow-y: auto;
  background-color: #fafafa;
  box-sizing: border-box; /* Critical: include padding in width */
}

/* Inner wrapper (80% width of parent) */
.chat-messages-inner {
  width: 100%; /* Matches 80% of container (due to 10% padding) */
  max-width: 1200px; /* Optional: limit max width for large screens */
  margin: 0 auto; /* Center content */
}

/* Message item */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 80%; /* Message bubble max width */
  animation: fadeIn 0.3s ease;
}

/* User message (right-aligned) */
.user-message {
  flex-direction: row-reverse;
  margin-left: auto;
}

/* AI message (left-aligned) */
.ai-message {
  margin-right: auto;
}

/* Highlighted message (for search) */
.highlighted {
  background-color: #fff3cd;
  border-radius: 8px;
  padding: 4px;
}

/* Avatar wrapper (prevent layout shift) */
.message-avatar-wrapper {
  width: 40px;
  height: 40px;
  flex-shrink: 0; /* Critical: keep avatar size fixed */
}

/* Avatar (FIXED: ensure visibility) */
.message-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover; /* Prevent image distortion */
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Message content wrapper */
.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Message content */
.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word; /* Wrap long text */
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

/* Attached files */
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

/* Animation */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Scrollbar styling */
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