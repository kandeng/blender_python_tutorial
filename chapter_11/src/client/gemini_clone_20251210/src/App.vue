<template>
  <div class="app-container">
    <Sidebar @menu-select="activeTab = $event" />
    <el-container class="main-container">
      <TopBar 
        :active-tab="activeTab"
        :user-avatar="userAvatar"
        @tab-change="activeTab = $event"
        @open-login="showLoginModal = true"
      />
      <MainContent
        :active-tab="activeTab"
        :chat-messages="chatMessages"
        v-model:message-input="messageInput"
        :upload-files="uploadFiles"
        :ai-avatar="aiAvatar"
        :user-avatar="userAvatar"
        @upload-file="handleFileUpload"
        @send-message="sendMessage"
      />
    </el-container>
    <LoginModal 
      v-model:show-modal="showLoginModal"
      @login-success="handleLoginSuccess"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from './components/layout/Sidebar.vue'
import TopBar from './components/layout/TopBar.vue'
import MainContent from './components/layout/MainContent.vue'
import LoginModal from './components/auth/LoginModal.vue'
import { useChatStore } from './composables/useChatStore'
import { useWebSocket } from './composables/useWebSocket'

const activeTab = ref('chatbot')
const userAvatar = ref('')
const showLoginModal = ref(false)

const {
  chatMessages,
  messageInput,
  uploadFiles,
  aiAvatar,
  handleFileUpload
  // ✅ Remove messagesContainer from destructuring
} = useChatStore()

const { sendMessage } = useWebSocket(chatMessages, uploadFiles)

const handleLoginSuccess = (avatarUrl) => {
  userAvatar.value = avatarUrl
  ElMessage.success('Welcome back!')
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Responsive Design */
@media (max-width: 768px) {
  .sidebar {
    width: 64px !important;
  }
  
  .top-bar {
    flex-direction: column;
    align-items: flex-start;
    padding: 10px;
  }
  
  .user-profile {
    align-self: flex-end;
    margin-top: -40px;
  }
}
</style>