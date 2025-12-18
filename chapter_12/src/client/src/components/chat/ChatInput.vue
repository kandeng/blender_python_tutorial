<!-- Message input + function panel -->
<template>
  <div class="chat-input-root" :class="$attrs.class">
    <!-- Resizer for input height -->
    <div 
      class="chat-resizer" 
      @mousedown="startResize"
      :class="{ dragging: isResizing }"
    ></div>

    <!-- Main input area -->
    <div class="chat-input-area" :style="{ height: inputHeight + 'px' }">
      <!-- Plus button (replace upload icon) -->
      <el-button 
        class="plus-btn" 
        @click="isFunctionPanelOpen = !isFunctionPanelOpen"
      >
        <img src="@/assets/icons/plus.svg" alt="Plus" class="icon" />
      </el-button>

      <!-- Message input -->
      <el-input
        v-model="localMessageInput"
        type="textarea"
        placeholder="Type your message here..."
        class="message-input"
        @keyup.enter="sendMessage"
        :autosize="false"
        :style="{ height: (inputHeight - 30) + 'px' }"
      ></el-input>

      <!-- Send button -->
      <el-button
        type="primary"
        class="send-btn"
        @click="sendMessage"
        :disabled="!localMessageInput?.trim() && uploadFiles.length === 0"
      >
        <img src="@/assets/icons/send.svg" alt="Send" class="send-btn-icon" />
      </el-button>
    </div>

    <!-- Function panel (slide down animation) -->
    <transition name="slide-down">
      <div class="function-panel" v-if="isFunctionPanelOpen">
        <div class="function-btn" @click="triggerFileUpload">
          <img src="@/assets/icons/upload.svg" alt="Upload" class="icon" />
          <span>Upload File</span>
        </div>
        <div class="function-btn" @click="openSearchDialog">
          <img src="@/assets/icons/search.svg" alt="Search" class="icon" />
          <span>Search Messages</span>
        </div>
      </div>
    </transition>

    <!-- File preview area (shows selected files) -->
    <div class="file-preview" v-if="uploadFiles.length > 0">
      <div 
        class="file-item" 
        v-for="(file, index) in uploadFiles" 
        :key="index"
        :data-file-id="index"
      >
        <div class="file-info">
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">({{ formatFileSize(file.size) }})</span>
        </div>
        <el-button 
          type="text" 
          size="small" 
          @click="removeFile(index)"
          class="remove-file-btn"
        >
          ×
        </el-button>
      </div>
    </div>

    <!-- Hidden file input (triggered by upload button) -->
    <input
      type="file"
      ref="fileInput"
      class="hidden-file-input"
      multiple
      accept=".jpg,.png,.mp3,.mp4,.pdf,.txt"
      @change="handleFileSelection"
    >

    <!-- Search dialog -->
    <el-dialog
      title="Search Chat Messages"
      v-model="isSearchDialogOpen"
      width="500px"
      destroy-on-close
    >
      <el-input
        v-model="searchQuery"
        placeholder="Enter keywords to search..."
        clearable
        @keyup.enter="performSearch"
        class="search-input"
      ></el-input>

      <!-- Search results -->
      <div class="search-results" v-if="searchResults.length">
        <div 
          class="search-result-item"
          v-for="(result, index) in searchResults"
          :key="index"
          @click="scrollToMessage(result.id)"
        >
          <div class="result-sender">{{ result.sender === 'user' ? 'You' : 'AI' }}:</div>
          <div class="result-content">{{ result.content }}</div>
        </div>
      </div>

      <!-- No results -->
      <div v-else-if="searchQuery.trim()" class="no-results">
        No matching messages found
      </div>

      <!-- Dialog footer -->
      <template #footer>
        <el-button @click="isSearchDialogOpen = false">Cancel</el-button>
        <el-button type="primary" @click="performSearch">Search</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

// Props definition
const props = defineProps({
  messageInput: {
    type: String,
    default: ''
  },
  uploadFiles: {
    type: Array,
    required: true,
    default: () => []
  },
  messages: {
    type: Array,
    default: () => []
  }
})

// Emit events
const emit = defineEmits([
  'update:messageInput',
  'upload-file',
  'send-message',
  'scroll-to-message'
])

// Reactive refs
const localMessageInput = ref(props.messageInput)
const isResizing = ref(false)
const inputHeight = ref(120)
const startY = ref(0)
const startHeight = ref(0)
const isFunctionPanelOpen = ref(false)
const fileInput = ref(null)
const isSearchDialogOpen = ref(false)
const searchQuery = ref('')
const searchResults = ref([])

// Sync local input with parent
watch(localMessageInput, (val) => emit('update:messageInput', val))
watch(() => props.messageInput, (val) => localMessageInput.value = val)

// Watch uploadFiles for changes (debug)
watch(
  () => props.uploadFiles,
  (newFiles) => {
    console.log('Upload files updated:', newFiles)
  },
  { deep: true }
)

// File upload handling
const triggerFileUpload = () => {
  fileInput.value.click()
  isFunctionPanelOpen.value = false // Close panel after click
}

const handleFileSelection = (e) => {
  const files = Array.from(e.target.files)
  if (files.length) {
    files.forEach(file => {
      if (file) emit('upload-file', file)
    })
    e.target.value = '' // Reset input to allow re-selection
  }
}

const removeFile = (index) => {
  emit('upload-file', null, index)
}

// File size formatter
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Message sending
const sendMessage = () => {
  const val = localMessageInput.value.trim()
  if (!val && props.uploadFiles.length === 0) return
  
  emit('send-message', val)
  localMessageInput.value = ''
}

// Search functionality
const openSearchDialog = () => {
  isSearchDialogOpen.value = true
  isFunctionPanelOpen.value = false // Close panel after click
  searchQuery.value = ''
  searchResults.value = []
}

const performSearch = () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  const query = searchQuery.value.toLowerCase()
  searchResults.value = props.messages.filter(msg => 
    msg.content.toLowerCase().includes(query)
  )
}

const scrollToMessage = (messageId) => {
  emit('scroll-to-message', messageId)
  isSearchDialogOpen.value = false
}

// Resize input height
const startResize = (e) => {
  isResizing.value = true
  startY.value = e.clientY
  startHeight.value = inputHeight.value
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

const handleResize = (e) => {
  if (!isResizing.value) return
  const deltaY = startY.value - e.clientY
  const newHeight = Math.max(80, Math.min(400, startHeight.value + deltaY))
  inputHeight.value = newHeight
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// Cleanup event listeners
onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
/* Root container */
.chat-input-root {
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-top: 1px solid #e6e6e6;
}

/* Resizer */
.chat-resizer {
  height: 4px;
  background-color: #e0e0e0;
  cursor: ns-resize;
  transition: background-color 0.2s ease;
  border-radius: 2px;
}

.chat-resizer:hover {
  background-color: #007bff;
}

.chat-resizer.dragging {
  background-color: #007bff;
  height: 6px;
}

/* Input area */
.chat-input-area {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
}

/* Plus button (perfect circle) */
.plus-btn {
  flex-shrink: 0;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box !important;
  border: 1px solid #e0e0e0 !important;
}

/* Message input */
.message-input {
  flex: 1;
  min-width: 0; /* Prevent overflow */
}

.message-input :deep(.el-textarea__inner) {
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  resize: none;
  padding: 12px;
  font-size: 15px;
  width: 100% !important;
  box-sizing: border-box;
}

/* Send button (perfect circle) */
.send-btn {
  flex-shrink: 0;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

/* Icons */
.icon, .send-btn-icon {
  width: 20px !important;
  height: 20px !important;
  object-fit: contain;
  display: block;
}

/* Function panel */
.function-panel {
  display: flex;
  gap: 15px;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
  border-bottom: 1px solid #e9ecef;
}

.function-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
}

.function-btn:hover {
  background-color: #e9ecef;
}

/* Slide animation for panel */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
  max-height: 100px;
  opacity: 1;
}

.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* File preview */
.file-preview {
  padding: 8px 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
  z-index: 10;
  width: 100%;
  box-sizing: border-box;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  margin: 2px 0;
  border-bottom: 1px dashed #eee;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-size: 14px;
  color: #333;
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: #666;
}

.remove-file-btn {
  font-size: 16px;
  color: #999;
  padding: 0 4px;
}

.remove-file-btn:hover {
  color: #ff4d4f;
}

/* Hidden file input */
.hidden-file-input {
  display: none;
}

/* Search dialog styles */
.search-input {
  margin-bottom: 15px;
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 10px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

.search-result-item {
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 8px;
}

.search-result-item:hover {
  background-color: #f0f0f0;
}

.result-sender {
  font-weight: 600;
  color: #007bff;
  margin-bottom: 4px;
}

.result-content {
  font-size: 14px;
  color: #333;
}

.no-results {
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

/* Override Element Plus button styles */
:deep(.el-button--circle) {
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  padding: 0 !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
</style>