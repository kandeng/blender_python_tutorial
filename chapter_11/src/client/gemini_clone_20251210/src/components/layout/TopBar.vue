<template>
  <el-header class="pinterest-top-bar">
    <!-- Pinterest-style tab navigation -->
    <div class="tab-container">
      <div 
        class="tab-item"
        v-for="tab in tabs" 
        :key="tab.name"
        :class="{ active: localActiveTab === tab.name }"
        @click="switchTab(tab.name)"
      >
        <el-icon :icon="tab.icon" class="tab-icon"></el-icon>
        <!-- Label wrapper for precise text/underbar alignment -->
        <div class="tab-label-container">
          <span class="tab-label">{{ tab.label }}</span>
        </div>
      </div>
    </div>

    <!-- User avatar (preserved) -->
    <div class="user-profile" @click="showLoginModal = true">
      <el-avatar :src="userAvatar" class="avatar" icon="User"></el-avatar>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ChatDotRound, Picture, FolderOpened } from '@element-plus/icons-vue'

// Tab config (unchanged)
const tabs = ref([
  { name: 'chatbot', label: '对话', icon: ChatDotRound },
  { name: 'gallery', label: '展厅', icon: Picture },
  { name: 'archive', label: '我的作品', icon: FolderOpened }
])

// Props & Emits (unchanged functionality)
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

const emit = defineEmits(['tab-change', 'open-login'])

const localActiveTab = ref(props.activeTab)
const showLoginModal = ref(false)

watch(
  () => props.activeTab,
  (newVal) => { localActiveTab.value = newVal },
  { immediate: true }
)

const switchTab = (tabName) => {
  localActiveTab.value = tabName
  emit('tab-change', tabName)
}

watch(showLoginModal, (val) => {
  if (val) emit('open-login')
})
</script>

<style scoped>
/* Base top bar */
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

/* Tab container */
.tab-container {
  display: flex;
  gap: 24px;
  align-items: center;
  height: 100%;
}

/* Individual tab item */
.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  padding: 0 4px;
  cursor: pointer;
  color: #333333;
  font-size: 16px;
  font-weight: 700; /* Bold text */
  transition: color 0.2s ease;
  position: relative;
}

/* Hover state */
.tab-item:hover {
  color: #e60023; /* Pinterest red */
}

/* Active tab text color */
.tab-item.active {
  color: #e60023;
}

/* --------------------------
   Critical: Text + Underbar Alignment
--------------------------- */
/* Label container (anchors text and underbar) */
.tab-label-container {
  display: flex;
  align-items: center;
  justify-content: center; /* Center text horizontally */
  position: relative;
  height: 100%; /* Match tab height for vertical centering */
}

/* Tab label (ensures text is centered) */
.tab-label {
  line-height: 1;
  text-align: center; /* Explicit text centering */
}

/* Active tab underbar (matches text width + centered under text) */
.tab-item.active .tab-label-container::after {
  content: '';
  position: absolute;
  bottom: 0; /* Align to bottom of tab bar */
  left: 0; /* Match text container's left edge */
  width: 100%; /* Exact width of text container */
  height: 4px; /* Pinterest-style thickness */
  background-color: #e60023; /* Pinterest red */
  border-radius: 2px 2px 0 0;
  /* Ensure underbar is centered relative to text */
  transform: none; /* No offset needed (matches text width) */
}

/* Tab icon (aligned with text) */
.tab-icon {
  font-size: 20px;
  align-self: center; /* Match text vertical alignment */
}

/* User avatar */
.user-profile {
  cursor: pointer;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

/* Reset Element Plus defaults */
:deep(.el-header) {
  border: none !important;
  padding: 0 !important;
}
</style>