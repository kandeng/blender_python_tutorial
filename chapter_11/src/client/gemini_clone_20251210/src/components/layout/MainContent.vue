<!-- Wrapper for tab content -->
<template>
  <el-main class="content-panel">
    <div v-if="activeTab === 'chatbot'" class="chatbot-panel">
      <ChatMessages
        :chat-messages="chatMessages"
        :ai-avatar="aiAvatar"
        :user-avatar="userAvatar"
      />
      <ChatInput
        :message-input="messageInput"
        @update:message-input="emit('update:message-input', $event)"
        :upload-files="uploadFiles"
        @upload-file="emit('upload-file', $event)"
        @send-message="emit('send-message', $event)"
      />
    </div>
    
    <!-- Gallery Panel -->
    <GalleryPanel v-if="activeTab === 'gallery'" />
    
    <!-- Archive Panel -->
    <ArchivePanel v-if="activeTab === 'archive'" />
    
    <!-- Fallback for unknown tabs -->
    <div v-else class="empty-panel">
      <el-empty description="No content available for this tab"></el-empty>
    </div>
  </el-main>
</template>

<script setup>

// Import components
import ChatMessages from '@/components/chat/ChatMessages.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import GalleryPanel from '@/components/gallery/GalleryPanel.vue'
import ArchivePanel from '@/components/archive/ArchivePanel.vue'

// ✅ Define props (all read-only)
const props = defineProps({
  activeTab: {
    type: String,
    required: true,
    default: 'chatbot'
  },
  chatMessages: {
    type: Array,
    required: true
  },
  messageInput: {  // Read-only prop from parent
    type: String,
    required: true
  },
  uploadFiles: {
    type: Array,
    required: true
  },
  aiAvatar: {
    type: String,
    required: true
  },
  userAvatar: {
    type: String,
    required: true
  }
})

// ✅ Define emits (forward all events to parent)
const emit = defineEmits([
  'update:message-input',  // For messageInput v-model
  'upload-file',           // For file uploads
  'send-message'           // For sending messages
])

// ❌ Remove local sendMessage/handleFileUpload (forward events directly)
</script>

<style scoped>
.content-panel {
  flex: 1;
  padding: 0;
  overflow: auto;
  background-color: #f9f9f9;
}

.chatbot-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.empty-panel {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

@media (max-width: 768px) {
  .message {
    max-width: 95%;
  }
}
</style>