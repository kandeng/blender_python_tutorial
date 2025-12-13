<!-- Wrapper for tab content -->
<template>
  <div class="main-content">
    <!-- Tab Content Switcher (preserve original logic) -->
    <div v-if="activeTab === 'chatbot'" class="chatbot-panel">
      <!-- Centered chat container (80% width like Gemini) -->
      <div class="chat-container">
        <!-- Chat Messages (import existing ChatMessages component) -->
        <ChatMessages 
          :bot-messages="botMessages" 
          :user-messages="userMessages"
          :chat-messages="chatMessages"
          :ai-avatar="aiAvatar || 'Robot'"
          :user-avatar="userAvatar || 'User'"
          class="chat-messages"
        />

        <!-- Chat Input with Draggable Resizer -->
        <ChatInput 
          :message-input="messageInput"
          :upload-files="uploadFiles"
          @update:messageInput="handleInputUpdate"
          @upload-file="handleFileUpload"
          @send-message="handleSendMessage"
        />
      </div>
    </div>

    <!-- Preserve original tabs (Gallery/Archive) -->
    <GalleryPanel v-else-if="activeTab === 'gallery'" />
    <ArchivePanel v-else-if="activeTab === 'archive'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatMessages from '../chat/ChatMessages.vue'
import ChatInput from '../chat/ChatInput.vue'
import GalleryPanel from '../gallery/GalleryPanel.vue'
import ArchivePanel from '../archive/ArchivePanel.vue'

// Preserve original props (no changes)
const props = defineProps({
  activeTab: {
    type: String,
    default: 'chatbot'
  },
  botMessages: {
    type: Array,
    default: () => []
  },
  userMessages: {
    type: Array,
    default: () => []
  },
  chatMessages: {
    type: Array,
    default: () => []
  },
  messageInput: {
    type: String,
    default: ''
  },
  uploadFiles: {
    type: Array,
    default: () => []
  }
})

// Preserve original emits (no changes)
const emit = defineEmits([
  'update:messageInput',
  'upload-file',
  'send-message'
])

// Preserve original handlers (no changes)
const handleInputUpdate = (val) => emit('update:messageInput', val)
const handleFileUpload = (file) => emit('upload-file', file)
const handleSendMessage = (val) => emit('send-message', val)

// Default avatars (add userAvatar here)
const aiAvatar = ref('Robot') // For AI/bot
const userAvatar = ref('User') // For user (new)
</script>

<style scoped>
/* Base main content */
.main-content {
  width: 100%;
  height: calc(100vh - 60px); /* Full height minus top bar */
  background-color: #f9f9f9; /* Match Gemini's light background */
  overflow: hidden;
}

/* Chatbot panel wrapper */
.chatbot-panel {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center; /* Center chat container horizontally */
  align-items: flex-start;
  padding: 20px 0;
}

/* Centered chat container (80% width like Gemini) */
.chat-container {
  width: 80%;
  max-width: 1200px; /* Prevent overstretching on large screens */
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Chat messages area (fills available space) */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Replace .chat-input-wrapper with this (targets ChatInput's root) */
:deep(.chat-input-root) {
  flex-shrink: 0;
}

/* Responsive adjustment (Gemini mobile style) */
@media (max-width: 768px) {
  .chat-container {
    width: 95%; /* Full width on mobile */
  }
}
</style>
