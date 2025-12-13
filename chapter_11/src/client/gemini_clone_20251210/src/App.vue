<template>
  <div class="app-container">
    <!-- Resizable Sidebar (sync collapse state) -->
    <div 
      class="sidebar-wrapper" 
      :style="{ width: isSidebarCollapsed ? '64px' : sidebarWidth + 'px' }"
    >
      <Sidebar 
        @menu-select="activeTab = $event"
        @collapse-change="handleSidebarCollapse" 
      />
    </div>

    <!-- Draggable Resizer (hidden when sidebar collapsed) -->
    <div 
      class="resizer" 
      @mousedown="startDrag"
      :class="{ dragging: isDragging }"
      v-if="!isSidebarCollapsed" 
    ></div>

    <!-- Main Content Area -->
    <el-container class="main-container">
      <TopBar 
        :active-tab="activeTab"
        :user-avatar="userAvatar"
        @tab-change="activeTab = $event"
        @open-login="showLoginModal = true"
      />
      
      <!-- Tab Content -->
      <div class="tab-content">
        <ChatPanel v-if="activeTab === 'chatbot'" :active="activeTab === 'chatbot'" />
        <GalleryPanel v-if="activeTab === 'gallery'" :active="activeTab === 'gallery'" />
        <ArchivePanel v-if="activeTab === 'archive'" :active="activeTab === 'archive'" />
      </div>
    </el-container>

    <LoginModal 
      v-model:show-modal="showLoginModal"
      @login-success="handleLoginSuccess"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from './components/layout/Sidebar.vue'
import TopBar from './components/layout/TopBar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import GalleryPanel from './components/gallery/GalleryPanel.vue'
import ArchivePanel from './components/archive/ArchivePanel.vue'
import LoginModal from './components/auth/LoginModal.vue'
import { useChatStore } from './composables/useChatStore'
import { useWebSocket } from './composables/useWebSocket'

// Sidebar state (sync collapse + resize)
const sidebarWidth = ref(260)
const resizerWidth = 4
const isDragging = ref(false)
const isSidebarCollapsed = ref(false) // Sync with Sidebar.vue
const startX = ref(0)
const startWidth = ref(0)

// Min/max width limits (only for expanded state)
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

// Sync collapse state from Sidebar.vue
const handleSidebarCollapse = (collapsed) => {
  isSidebarCollapsed.value = collapsed
}

// Resizer logic (only for expanded state)
const startDrag = (e) => {
  if (isSidebarCollapsed.value) return
  isDragging.value = true
  startX.value = e.clientX
  startWidth.value = sidebarWidth.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

const handleDrag = (e) => {
  if (!isDragging.value || isSidebarCollapsed.value) return
  const deltaX = e.clientX - startX.value
  const newWidth = startWidth.value + deltaX
  if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
    sidebarWidth.value = newWidth
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Event listeners
onMounted(() => {
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
})

// Reset width when expanding sidebar
watch(isSidebarCollapsed, (collapsed) => {
  if (!collapsed && sidebarWidth.value < MIN_WIDTH) {
    sidebarWidth.value = 260 // Reset to default expanded width
  }
})

const handleLoginSuccess = (avatarUrl) => {
  userAvatar.value = avatarUrl
  ElMessage.success('Welcome back!')
}
</script>

<style scoped>
.tab-content {
  flex: 1;
  overflow: hidden;
  height: calc(100% - 60px); /* Subtract header height */
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  padding: 0;
  margin: 0;
}

/* Sidebar Wrapper (fixed collapsed width) */
.sidebar-wrapper {
  flex-shrink: 0;
  height: 100%;
  transition: width 0.3s ease;
}

/* Draggable Resizer */
.resizer {
  width: v-bind(resizerWidth + 'px');
  height: 100%;
  background-color: #e5e7eb;
  cursor: col-resize;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}
.resizer:hover {
  background-color: #cbd5e1;
}
.resizer.dragging {
  background-color: #94a3b8;
}

/* Main Chatbot Panel */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden;
}

/* Override Element Plus defaults */
:deep(.el-aside) {
  padding: 0 !important;
  margin: 0 !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .sidebar-wrapper {
    width: 64px !important;
  }
  .resizer {
    display: none;
  }
}
</style>