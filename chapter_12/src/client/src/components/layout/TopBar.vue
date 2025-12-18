<template>
  <el-header class="pinterest-top-bar">
    <!-- Pinterest-style tab navigation -->
    <div class="tab-container">
      <div 
        class="tab-item"
        v-for="tab in tabs" 
        :key="tab.name"
        :class="{ active: activeTab === tab.name }"
        @click="switchTab(tab.name)"
      >
        <el-icon :icon="tab.icon" class="tab-icon"></el-icon>
        <div class="tab-label-container">
          <span class="tab-label">{{ tab.label }}</span>
        </div>
      </div>
    </div>

    <!-- User avatar -->
    <div class="user-profile" @click="showLoginModal = true">
      <el-avatar :src="userAvatar" class="avatar" icon="User"></el-avatar>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ChatDotRound, Picture, FolderOpened } from '@element-plus/icons-vue'

// Tab configuration
const tabs = ref([
  { name: 'chatbot', label: '对话', icon: ChatDotRound },
  { name: 'gallery', label: '展厅', icon: Picture },
  { name: 'archive', label: '我的作品', icon: FolderOpened }
])

// Props
const props = defineProps({
  activeTab: {
    type: String,
    default: 'chatbot'
  },
  userAvatar: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['tab-change', 'open-login'])

// Local state
const showLoginModal = ref(false)

// Handle tab switching
const switchTab = (tabName) => {
  if (tabName !== props.activeTab) {
    emit('tab-change', tabName)
  }
}

// Watch for login modal changes
watch(showLoginModal, (val) => {
  if (val) emit('open-login')
})
</script>

<style scoped>
/* All styles remain the same */
.pinterest-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: #ffffff;
  height: 60px;
  box-shadow: none;
  border: none;
}

.tab-container {
  display: flex;
  gap: 24px;
  align-items: center;
  height: 100%;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  padding: 0 4px;
  cursor: pointer;
  color: #333333;
  font-size: 16px;
  font-weight: 700;
  transition: color 0.2s ease;
  position: relative;
}

.tab-item:hover {
  color: #e60023;
}

.tab-item.active {
  color: #e60023;
}

.tab-label-container {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 100%;
}

.tab-label {
  line-height: 1;
  text-align: center;
}

.tab-item.active .tab-label-container::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background-color: #e60023;
  border-radius: 2px 2px 0 0;
}

.tab-icon {
  font-size: 20px;
  align-self: center;
}

.user-profile {
  cursor: pointer;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

:deep(.el-header) {
  border: none !important;
  padding: 0 !important;
}
</style>