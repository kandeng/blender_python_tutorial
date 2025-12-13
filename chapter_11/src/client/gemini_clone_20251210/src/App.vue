<template>
  <div class="app-container">
    <!-- Sidebar (resizable width) -->
    <div class="sidebar-wrapper" :style="{ width: sidebarWidth + 'px' }">
      <Sidebar @menu-select="activeTab = $event" />
    </div>

    <!-- Draggable Vertical Resizer -->
    <div 
      class="resizer" 
      @mousedown="startDrag"
      :class="{ dragging: isDragging }"
    ></div>

    <!-- Main Chatbot Panel (no extra margin) -->
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
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from './components/layout/Sidebar.vue'
import TopBar from './components/layout/TopBar.vue'
import MainContent from './components/layout/MainContent.vue'
import LoginModal from './components/auth/LoginModal.vue'
import { useChatStore } from './composables/useChatStore'
import { useWebSocket } from './composables/useWebSocket'

// Sidebar resizing state
const sidebarWidth = ref(260)
const resizerWidth = 4 // Resizer line width
const isDragging = ref(false)
const startX = ref(0)
const startWidth = ref(0)

// Min/max sidebar width limits
const MIN_WIDTH = 200
const MAX_WIDTH = 500

// Original component state
const activeTab = ref('chatbot')
const userAvatar = ref('')
const showLoginModal = ref(false)

const {
  chatMessages,
  messageInput,
  uploadFiles,
  aiAvatar,
  handleFileUpload
} = useChatStore()

const { sendMessage } = useWebSocket(chatMessages, uploadFiles)

// Resizer logic (fixed drag calculation)
const startDrag = (e) => {
  isDragging.value = true
  startX.value = e.clientX
  startWidth.value = sidebarWidth.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

const handleDrag = (e) => {
  if (!isDragging.value) return
  const deltaX = e.clientX - startX.value
  const newWidth = startWidth.value + deltaX
  // Constrain width to min/max
  if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
    sidebarWidth.value = newWidth
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Event listener cleanup
onMounted(() => {
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
})

const handleLoginSuccess = (avatarUrl) => {
  userAvatar.value = avatarUrl
  ElMessage.success('Welcome back!')
}
</script>

<style scoped>
/* Core layout fix: flex-based, no extra margins */
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  padding: 0;
  margin: 0;
}

/* Sidebar wrapper (resizable, no extra padding) */
.sidebar-wrapper {
  flex-shrink: 0; /* Prevent sidebar from shrinking */
  height: 100%;
  padding: 0;
  margin: 0;
  transition: width 0.1s ease; /* Smooth resize */
}

/* Draggable resizer (no absolute positioning) */
.resizer {
  width: v-bind(resizerWidth + 'px');
  height: 100%;
  background-color: #e5e7eb;
  cursor: col-resize;
  flex-shrink: 0; /* Prevent resizer from shrinking */
  transition: background-color 0.2s ease;
}

.resizer:hover {
  background-color: #cbd5e1;
}

.resizer.dragging {
  background-color: #94a3b8;
}

/* Main chatbot panel (fill remaining space, no margin) */
.main-container {
  flex: 1; /* Critical: fill all remaining space */
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 0 !important; /* Remove Element Plus default padding */
  margin: 0 !important;
  overflow: hidden;
}

/* Mobile responsive fix */
@media (max-width: 768px) {
  .sidebar-wrapper {
    width: 64px !important;
  }
  .resizer {
    display: none;
  }
}

/* Remove deep styles for sidebar (no extra padding) */
:deep(.el-aside) {
  padding: 0 !important;
  margin: 0 !important;
}
</style>
