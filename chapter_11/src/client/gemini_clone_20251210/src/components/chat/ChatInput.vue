<!-- Message input + file upload -->
<template>
  <div class="chat-input-area">
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
    <!-- ✅ Use v-model on LOCAL reactive variable (not prop) -->
    <el-input
      v-model="localMessageInput"
      type="textarea"
      placeholder="Type your message here... (supports JPG/PNG/MP3/MP4/PDF)"
      class="message-input"
      @keyup.enter="sendMessage"
    ></el-input>
    <el-button
      type="primary"
      icon="PaperPlaneFilled"
      class="send-btn"
      @click="sendMessage"
      :disabled="!localMessageInput?.trim() && uploadFiles.length === 0"
      circle
    ></el-button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

// ✅ Define read-only props (from parent)
const props = defineProps({
  messageInput: {
    type: String,
    required: true
  },
  uploadFiles: {
    type: Array,
    required: true
  }
})

// ✅ Define emits to communicate with parent
const emit = defineEmits([
  'update:messageInput', // For syncing input value
  'upload-file',         // For file uploads
  'send-message'         // For sending messages
])

// ✅ Local reactive variable (mirrors parent's messageInput prop)
const localMessageInput = ref(props.messageInput)

// ✅ Sync parent prop changes to local variable (if parent updates the value)
watch(
  () => props.messageInput,
  (newValue) => {
    localMessageInput.value = newValue
  }
)

// ✅ Sync local variable changes back to parent (optional, for real-time sync)
watch(
  localMessageInput,
  (newValue) => {
    emit('update:messageInput', newValue)
  }
)

// Handle file upload (forward to parent)
const handleFileUpload = (file) => {
  emit('upload-file', file)
}

// Handle send message (forward to parent + reset local input)
const sendMessage = () => {
  const inputValue = localMessageInput.value.trim()
  
  // Guard clause (check trimmed string + files)
  if (!inputValue && props.uploadFiles.length === 0) return
  
  // Emit message to parent (use the trimmed value)
  emit('send-message', inputValue)
  
  // Reset local input (updates parent via watch)
  localMessageInput.value = ''
}
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
}

.message-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
}
</style>