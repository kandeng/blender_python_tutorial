<!-- Message input + file upload -->
<template>
  <div class="chat-input-root" :class="$attrs.class">
    <div 
      class="chat-resizer" 
      @mousedown="startResize"
      :class="{ dragging: isResizing }"
    ></div>

    <div class="chat-input-area" :style="{ height: inputHeight + 'px' }">
      <el-upload
        class="upload-btn"
        :auto-upload="false"
        :on-change="handleFileUpload"
        :file-list="uploadFiles"
        multiple
        accept=".jpg,.png,.mp3,.mp4,.pdf"
      >
        <el-button class="upload-btn__circle" circle>
          <img src="@/assets/icons/upload.svg" alt="Upload" class="icon" />
        </el-button>
      </el-upload>

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
  </div>
</template>

<script setup>
// Keep ALL existing script code (no changes)
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  messageInput: {
    type: String,
    default: ''
  },
  uploadFiles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'update:messageInput',
  'upload-file',
  'send-message'
])

const localMessageInput = ref(props.messageInput)
const isResizing = ref(false)
const inputHeight = ref(120)
const startY = ref(0)
const startHeight = ref(0)

watch(localMessageInput, (val) => emit('update:messageInput', val))
watch(() => props.messageInput, (val) => localMessageInput.value = val)

const handleFileUpload = (file) => emit('upload-file', file)

const sendMessage = () => {
  const val = localMessageInput.value.trim()
  if (!val && props.uploadFiles.length === 0) return
  emit('send-message', val)
  localMessageInput.value = ''
}

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
  /* Ensure equal dimensions for perfect circle */
  width: 40px;
  height: 40px;
  border-radius: 50%; /* Critical for circle shape */
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  width: 40px;  /* Add this - critical for circle */
  height: 40px; /* Add this - must equal width */
}

.icon, .send-btn-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

/* Optional: Reset Element Plus button styles */
:deep(.el-button--circle) {
  border-radius: 50% !important;
  width: 40px !important;
  height: 40px !important;
  padding: 0 !important;
}


/* Add styles for the new root container (matches original layout) */
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

.message-input :deep(.el-textarea__inner) {
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  resize: none;
  padding: 12px;
  font-size: 15px;
}
</style>