<template>
  <div class="app-container">
    <!-- Sidebar (Function Navigation Panel) -->
    <el-aside
      :width="isSidebarCollapsed ? '64px' : '240px'"
      class="sidebar"
      transition="width-collapse"
    >
      <!-- Collapse Toggle Button (100% valid icon string) -->
      <el-button
        @click="isSidebarCollapsed = !isSidebarCollapsed"
        class="collapse-btn"
        circle
        icon="Menu"
      ></el-button>

      <!-- Function Navigation List (native icon strings) -->
      <el-menu
        default-active="1"
        class="sidebar-menu"
        :collapse="isSidebarCollapsed"
        collapse-transition
      >
        <el-menu-item index="1" icon="ChatDotRound">
          <template #title>Chatbot</template>
        </el-menu-item>
        <el-menu-item index="2" icon="Picture">
          <template #title>Gallery</template>
        </el-menu-item>
        <el-menu-item index="3" icon="FolderOpened">
          <template #title>My Archive</template>
        </el-menu-item>
        <el-menu-item index="4" icon="Setting">
          <template #title>Settings</template>
        </el-menu-item>
        <el-menu-item index="5" icon="HelpFilled">
          <template #title>Help</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content Area -->
    <el-container class="main-container">
      <!-- Top Bar with Tabs & User Profile -->
      <el-header class="top-bar">
        <!-- Tab Navigation -->
        <el-tabs
          v-model="activeTab"
          class="top-tabs"
          type="card"
          @tab-change="handleTabChange"
        >
          <el-tab-pane name="chatbot">
            <template #label>
              <el-icon icon="ChatDotRound"></el-icon>
              Chatbot
            </template>
          </el-tab-pane>
          <el-tab-pane name="gallery">
            <template #label>
              <el-icon icon="Picture"></el-icon>
              Gallery
            </template>
          </el-tab-pane>
          <el-tab-pane name="archive">
            <template #label>
              <el-icon icon="FolderOpened"></el-icon>
              My Archive
            </template>
          </el-tab-pane>
        </el-tabs>

        <!-- User Profile Thumbnail -->
        <div class="user-profile" @click="showLoginModal = true">
          <el-avatar
            :src="userAvatar"
            class="avatar"
            icon="User"
          ></el-avatar>
        </div>
      </el-header>

      <!-- Main Content Panel -->
      <el-main class="content-panel">
        <!-- Chatbot Panel -->
        <div v-if="activeTab === 'chatbot'" class="chatbot-panel">
          <!-- Chat Messages Container -->
          <div class="chat-messages" ref="messagesContainer">
            <div v-for="(msg, index) in chatMessages" :key="index" :class="['message', msg.sender]">
              <el-avatar 
                :src="msg.sender === 'ai' ? aiAvatar : userAvatar" 
                class="message-avatar"
                :icon="msg.sender === 'ai' ? 'Monitor' : 'User'"
              ></el-avatar>
              <div class="message-content">
                <p>{{ msg.content }}</p>
                <!-- File Preview -->
                <div v-if="msg.files.length" class="file-preview">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item 
                      v-for="file in msg.files" 
                      :key="file.name" 
                      label="Attached File"
                    >
                      <el-link 
                        :download="file.name" 
                        :href="URL.createObjectURL(file)" 
                        type="primary"
                      >
                        <el-icon icon="Download"></el-icon> {{ file.name }} ({{ formatFileSize(file.size) }})
                      </el-link>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>
            </div>
          </div>

          <!-- Chat Input Area -->
          <div class="chat-input-area">
            <!-- File Upload Button -->
            <el-upload
              class="upload-btn"
              :auto-upload="false"
              :on-change="handleFileUpload"
              :file-list="uploadFiles"
              multiple
              accept=".jpg,.png,.mp3,.mp4,.pdf"
            >
              <el-button icon="UploadFilled" circle></el-button>
            </el-upload>

            <!-- Message Input -->
            <el-input
              v-model="messageInput"
              type="textarea"
              placeholder="Type your message here... (supports JPG/PNG, MP3, MP4, PDF)"
              class="message-input"
              @keyup.enter="sendMessage"
            ></el-input>

            <!-- Send Button (100% valid icon string) -->
            <el-button
              type="primary"
              icon="PaperPlaneFilled"
              class="send-btn"
              @click="sendMessage"
              :disabled="!messageInput.trim() && uploadFiles.length === 0"
              circle
            ></el-button>
          </div>
        </div>

        <!-- Gallery Panel -->
        <div v-if="activeTab === 'gallery'" class="gallery-panel">
          <el-row :gutter="20">
            <el-col 
              :xs="12" 
              :sm="8" 
              :md="6" 
              :lg="4" 
              v-for="(image, index) in galleryImages" 
              :key="index"
            >
              <el-card class="gallery-card">
                <el-image
                  :src="image.url"
                  fit="cover"
                  class="gallery-image"
                  :preview-src-list="getGalleryPreviewUrls()"
                ></el-image>
                <div class="gallery-card-footer">
                  <span>{{ image.title }}</span>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- My Archive Panel -->
        <div v-if="activeTab === 'archive'" class="archive-panel">
          <el-table :data="archiveItems" border style="width: 100%">
            <el-table-column prop="title" label="Title" min-width="200"></el-table-column>
            <el-table-column prop="date" label="Created Date" width="180"></el-table-column>
            <el-table-column prop="type" label="Type" width="100"></el-table-column>
            <el-table-column prop="actions" label="Actions" width="150">
              <template #default>
                <el-button type="primary" size="small" icon="Edit"></el-button>
                <el-button type="danger" size="small" icon="Delete"></el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-main>
    </el-container>

    <!-- Login/Register Modal -->
    <el-dialog
      v-model="showLoginModal"
      title="User Authentication"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="authTab" type="card">
        <el-tab-pane name="login" label="Login">
          <el-form :model="loginForm" label-width="80px">
            <el-form-item label="Email">
              <el-input v-model="loginForm.email" type="email"></el-input>
            </el-form-item>
            <el-form-item label="Password">
              <el-input v-model="loginForm.password" type="password"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin">Login</el-button>
              <el-button @click="showLoginModal = false">Cancel</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane name="register" label="Register">
          <el-form :model="registerForm" label-width="80px">
            <el-form-item label="Name">
              <el-input v-model="registerForm.name"></el-input>
            </el-form-item>
            <el-form-item label="Email">
              <el-input v-model="registerForm.email" type="email"></el-input>
            </el-form-item>
            <el-form-item label="Password">
              <el-input v-model="registerForm.password" type="password"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleRegister">Register</el-button>
              <el-button @click="showLoginModal = false">Cancel</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'

// ❌ NO DIRECT ICON IMPORTS (eliminates all export errors)
// All icons use Element Plus's native icon string system

// Sidebar State
const isSidebarCollapsed = ref(false)

// Tab State
const activeTab = ref('chatbot')
const handleTabChange = (tab) => {
  console.log('Switched to tab:', tab)
}

// User Profile & Login Modal
const userAvatar = ref('')
const showLoginModal = ref(false)
const authTab = ref('login')
const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ name: '', email: '', password: '' })

const handleLogin = () => {
  ElMessage.success('Login successful!')
  userAvatar.value = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
  showLoginModal.value = false
}

const handleRegister = () => {
  ElMessage.success('Registration successful! Please login.')
  authTab.value = 'login'
}

// Chatbot State
const chatMessages = ref([
  { sender: 'ai', content: 'Hello! How can I help you today?', files: [] }
])
const messageInput = ref('')
const uploadFiles = ref([])
const messagesContainer = ref(null)
const aiAvatar = ref('https://cube.elemecdn.com/6/94/4d3ea53c084bad6931a56d55811281jpeg.jpeg')

// Handle File Upload
const handleFileUpload = (file) => {
  uploadFiles.value.push(file.raw)
}

// Format File Size
const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / 1048576).toFixed(2)} MB`
}

// Send Message
const sendMessage = () => {
  if (!messageInput.value.trim() && uploadFiles.value.length === 0) return

  chatMessages.value.push({
    sender: 'user',
    content: messageInput.value.trim(),
    files: [...uploadFiles.value]
  })

  messageInput.value = ''
  uploadFiles.value = []

  // Simulate AI Response
  setTimeout(() => {
    chatMessages.value.push({
      sender: 'ai',
      content: 'Thank you for your message! I\'m processing your request and will respond shortly.',
      files: []
    })
  }, 1000)
}

// Auto-scroll to bottom
watch(chatMessages, () => {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 0)
})

// Gallery Data
const galleryImages = ref([
  { url: 'https://picsum.photos/800/600?random=1', title: 'Landscape Photo 1' },
  { url: 'https://picsum.photos/800/600?random=2', title: 'Portrait Photo 2' },
  { url: 'https://picsum.photos/800/600?random=3', title: 'Nature Photo 3' },
  { url: 'https://picsum.photos/800/600?random=4', title: 'City Photo 4' },
  { url: 'https://picsum.photos/800/600?random=5', title: 'Animal Photo 5' },
  { url: 'https://picsum.photos/800/600?random=6', title: 'Architecture Photo 6' }
])

// Computed for gallery preview URLs (avoids inline expression errors)
const getGalleryPreviewUrls = computed(() => {
  return galleryImages.value.map(img => img.url)
})

// Archive Data
const archiveItems = ref([
  { title: 'Project Proposal', date: '2025-01-10', type: 'Document' },
  { title: 'Client Meeting Notes', date: '2025-01-08', type: 'Notes' },
  { title: 'Design Mockups', date: '2025-01-05', type: 'Images' },
  { title: 'Audio Recording', date: '2025-01-03', type: 'Audio' },
  { title: 'Video Presentation', date: '2025-01-01', type: 'Video' }
])
</script>

<style scoped>
/* Base Layout */
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  transition: width 0.3s ease;
}

.collapse-btn {
  margin: 16px;
  background-color: #409eff;
  color: white;
}

.sidebar-menu {
  border-right: none;
  height: calc(100% - 80px);
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Top Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: white;
  border-bottom: 1px solid #e6e6e6;
}

.top-tabs {
  flex: 1;
}

.user-profile {
  cursor: pointer;
}

.avatar {
  width: 40px;
  height: 40px;
}

/* Content Panel */
.content-panel {
  flex: 1;
  padding: 0;
  overflow: auto;
  background-color: #f9f9f9;
}

/* Chatbot Panel */
.chatbot-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.message {
  display: flex;
  margin-bottom: 20px;
  max-width: 80%;
}

.message.ai {
  align-self: flex-start;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  margin-right: 10px;
  margin-left: 10px;
}

.message-content {
  background-color: white;
  padding: 10px 15px;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.file-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e6e6e6;
}

.chat-input-area {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e6e6e6;
  gap: 10px;
}

.upload-btn {
  flex-shrink: 0;
}

.message-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
}

/* Gallery Panel */
.gallery-panel {
  padding: 20px;
}

.gallery-card {
  height: 250px;
  margin-bottom: 20px;
}

.gallery-image {
  height: 200px;
  width: 100%;
}

.gallery-card-footer {
  text-align: center;
  padding: 5px;
}

/* Archive Panel */
.archive-panel {
  padding: 20px;
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
  
  .message {
    max-width: 95%;
  }
}
</style>
