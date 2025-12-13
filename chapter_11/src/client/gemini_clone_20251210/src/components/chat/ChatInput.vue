<!-- Message input + function panel -->
<template>
  <div class="chat-input-root" :class="$attrs.class">
    <div 
      class="chat-resizer" 
      @mousedown="startResize"
      :class="{ dragging: isResizing }"
    ></div>

    <div class="chat-input-area" :style="{ height: inputHeight + 'px' }">
      <!-- Plus button to toggle function panel -->
      <el-button 
        class="plus-btn" 
        circle 
        @click="isFunctionPanelOpen = !isFunctionPanelOpen"
      >
        <img src="@/assets/icons/plus.svg" alt="Plus" class="icon" />
      </el-button>

      <el-input
        v-model="localMessageInput"
        type="textarea"
        placeholder="Type your message here..."
        class="message-input"
        @keyup.enter="sendMessage"
        :autosize="false"
        :style="{ height: (inputHeight - 30) + 'px' }"
      ></el-input>

      <el-button
        type="primary"
        class="send-btn"
        @click="sendMessage"
        :disabled="!localMessageInput?.trim() && uploadFiles.length === 0"
        circle
      >
        <img src="@/assets/icons/send.svg" alt="Send" class="send-btn-icon" />
      </el-button>
    </div>

    <!-- Function panel (expands below input) -->
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

    <!-- Hidden file input for upload -->
    <input
      type="file"
      ref="fileInput"
      class="hidden-file-input"
      multiple
      accept=".jpg,.png,.mp3,.mp4,.pdf"
      @change="handleFileSelection"
    >

    <!-- Search dialog -->
    <el-dialog
      title="Search Messages"
      v-model="isSearchDialogOpen"
      :width="500"
    >
      <el-input
        v-model="searchQuery"
        placeholder="Enter keywords to search..."
        @keyup.enter="performSearch"
      ></el-input>
      <div class="search-results" v-if="searchResults.length">
        <div 
          class="search-result-item"
          v-for="(result, index) in searchResults"
          :key="index"
          @click="scrollToMessage(result.id)"
        >
          {{ result.content }}
        </div>
      </div>
      <div v-else-if="searchQuery" class="no-results">
        No matching messages found
      </div>
      <template #footer>
        <el-button @click="isSearchDialogOpen = false">Cancel</el-button>
        <el-button type="primary" @click="performSearch">Search</el-button>
      </template>
    </el-dialog>

    <!-- File preview area -->
    <div class="file-preview" v-if="uploadFiles.length">
      <div class="file-item" v-for="(file, index) in uploadFiles" :key="index">
        <span>{{ file.name }}</span>
        <el-button 
          type="text" 
          size="small" 
          @click="removeFile(index)"
        >
          Remove
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  messageInput: {
    type: String,
    default: ''
  },
  uploadFiles: {
    type: Array,
    default: () => []
  },
  // New prop to receive all messages for search functionality
  messages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'update:messageInput',
  'upload-file',
  'send-message',
  'scroll-to-message' // New emit for scroll functionality
])

// Refs
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

// Watchers
watch(localMessageInput, (val) => emit('update:messageInput', val))
watch(() => props.messageInput, (val) => localMessageInput.value = val)

// File handling
const triggerFileUpload = () => {
  fileInput.value.click()
  isFunctionPanelOpen.value = false // Close panel after clicking
}

const handleFileSelection = (e) => {
  if (e.target.files.length) {
    Array.from(e.target.files).forEach(file => {
      emit('upload-file', file)
    })
    // Reset file input to allow re-selection of same file
    e.target.value = ''
  }
}

const removeFile = (index) => {
  emit('upload-file', null, index) // Null indicates removal
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
  isFunctionPanelOpen.value = false // Close panel after clicking
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

// Resize handling
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

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
.plus-btn {
  flex-shrink: 0;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important; /* Force perfect circle */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 !important; /* Remove Element Plus default padding */
  margin: 0 !important;
  border: none !important; /* Remove default border if needed */
  box-sizing: border-box !important;
}

/* Fix Send Button (Perfect Circle) */
.send-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 !important; /* Critical: remove default padding */
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important; /* Force perfect circle */
  margin: 0 !important;
  box-sizing: border-box !important;
}

/* Fix Icon Alignment in Circles */
.icon, .send-btn-icon {
  width: 20px !important;
  height: 20px !important;
  object-fit: contain;
  display: block; /* Prevent icon from stretching button */
}

/* Prevent Input Box from Pushing Buttons (Optional Layout Safeguard) */
.chat-input-area {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e6e6e6;
  gap: 10px;
  width: 100%;
  box-sizing: border-box; /* Ensure padding doesn't break width */
}

.message-input {
  flex: 1;
  min-width: 0; /* Critical: prevent input from overflowing and squeezing buttons */
}

/* Function panel styles */
.function-panel {
  display: flex;
  gap: 15px;
  padding: 10px 15px;
  background-color: white;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #e6e6e6;
}

.function-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.function-btn:hover {
  background-color: #f5f5f5;
}

/* Animation for panel */
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

/* Hidden file input */
.hidden-file-input {
  display: none;
}

/* File preview styles */
.file-preview {
  padding: 10px 15px;
  background-color: #fafafa;
  border-top: 1px solid #f0f0f0;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 14px;
}

/* Search dialog styles */
.search-results {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

.search-result-item {
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: #f0f0f0;
}

.no-results {
  padding: 15px;
  text-align: center;
  color: #666;
}

/* Resizer and root styles */
.chat-input-root {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.chat-resizer {
  height: 4px;
  background-color: #e0e0e0;
  cursor: ns-resize;
  transition: background-color 0.2s ease;
  border-radius: 2px;
  margin: 0;
}

.chat-resizer:hover {
  background-color: #007bff;
}

.chat-resizer.dragging {
  background-color: #007bff;
  height: 6px;
}

/* Override Element Plus Button Defaults (Critical Fix) */
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

/* Fix Textarea Inner Styles (Prevent Layout Shifts) */
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
</style>