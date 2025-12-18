<!-- Single chat message (AI/user) -->
<template>
  <div :class="['message', msg.sender]">
    <el-avatar 
      :src="msg.sender === 'ai' ? aiAvatar : userAvatar" 
      class="message-avatar"
      :icon="(msg.sender === 'ai' && !aiAvatar) ? Monitor : (!userAvatar ? User : null)"
    ></el-avatar>

    <div class="message-content">
      <p>{{ msg.content }}</p>
      <!-- File Preview -->
      <div v-if="hasFiles(msg)" class="file-preview">
        <el-descriptions :column="1" border>
          <el-descriptions-item 
            v-for="(file, fileIndex) in msg.files" 
            :key="fileIndex" 
            label="Attached File"
          >
            <el-link 
              v-if="isValidFile(file)" 
              :download="getFileName(file)" 
              :href="getFileUrl(file)" 
              type="primary"
            >
              <el-icon icon="Download"></el-icon> {{ getFileName(file) }} ({{ formatFileSize(getFileSize(file)) }})
            </el-link>
            <span v-else>
              <el-icon icon="File"></el-icon> {{ getFileName(file) }} ({{ formatFileSize(getFileSize(file)) }})
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </div>
</template>


<script setup>
import { useFileHelpers } from '../../composables/useFileHelpers.js'
import { Monitor, User } from '@element-plus/icons-vue' 

const props = defineProps({
  msg: {
    type: Object,
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

// Use file helpers
const { hasFiles, isValidFile, getFileName, getFileSize, getFileUrl, formatFileSize } = useFileHelpers()
</script>


<style scoped>
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
</style>