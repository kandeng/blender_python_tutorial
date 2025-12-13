<!--  Sidebar (navigation) -->
<template>
  <el-aside 
    class="sidebar" 
    transition="width-collapse"
    :style="{ width: isSidebarCollapsed ? '64px' : 'auto' }"
  >
    <!-- Collapse Toggle Button (inside sidebar) -->
    <div class="collapse-btn-wrapper">
      <el-button
        @click="isSidebarCollapsed = !isSidebarCollapsed"
        class="collapse-btn"
        circle
        icon="Menu"
      ></el-button>
    </div>

    <!-- Main Content Area (constrained width) -->
    <div class="sidebar-content">
      <!-- New Topic Button (HIDDEN when collapsed) -->
      <div class="new-topic-btn-wrapper" v-if="!isSidebarCollapsed">
        <el-button 
          class="new-topic-btn" 
          icon="CirclePlus"
          @click="handleNewTopic"
        >
          开始新话题
        </el-button>
      </div>

      <!-- Search Input (collapsible + taller) -->
      <el-input
        v-if="!isSidebarCollapsed"
        placeholder="搜索以往话题"
        class="search-input"
        prefix-icon="Search"
        size="small"
      ></el-input>

      <!-- Divider + Title (collapsible) -->
      <div v-if="!isSidebarCollapsed" class="history-header">
        <div class="divider"></div>
        <div class="title-wrapper">
          <el-icon class="clock-icon"><Clock /></el-icon>
          <span class="title-text">历史对话</span>
        </div>
      </div>

      <!-- Historic Topics List (HIDDEN when collapsed) -->
      <el-scrollbar 
        class="history-container" 
        v-if="!isSidebarCollapsed"
      >
        <el-menu
          default-active="1"
          class="history-menu"
          collapse-transition
          @select="handleMenuSelect"
          size="small"
        >
          <el-menu-item index="1">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">Chatbot Vue3 page</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="2">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">比较主流开源AI代理框架</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="3">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">手机版对话</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="4">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">前端性能优化方案</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="5">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">Vue3组合式API实践</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="6">
            <template #title>
              <div class="topic-item">
                <span class="topic-text">Element Plus主题定制</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </div>
  </el-aside>
</template>

<script setup>
// ✅ Add missing import for watch
import { ref, watch } from 'vue'
import { Clock } from '@element-plus/icons-vue'

// Emit events to parent (App.vue)
const emit = defineEmits(['menu-select', 'new-topic', 'collapse-change'])

// Sidebar collapse state
const isSidebarCollapsed = ref(false)

// Handle topic selection
const handleMenuSelect = (index) => {
  emit('menu-select', index)
}

// Handle new topic button click
const handleNewTopic = () => {
  emit('new-topic')
}

// Emit collapse state change to App.vue
const watchCollapse = () => {
  emit('collapse-change', isSidebarCollapsed.value)
}
// Watch for collapse state changes
watch(isSidebarCollapsed, watchCollapse)
</script>

<style scoped>
/* Core Sidebar Styles */
.sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden !important;
  min-width: 64px !important;
  max-width: 500px !important;
}

/* Collapse Button Wrapper (center button in collapsed state) */
.collapse-btn-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* Collapse Toggle Button (inside sidebar) */
.collapse-btn {
  background-color: #409eff;
  color: white;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  margin: 0 !important;
}

/* Sidebar Content Wrapper (constrained width) */
.sidebar-content {
  padding: 0 12px !important;
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100% !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
}

/* New Topic Button Wrapper */
.new-topic-btn-wrapper {
  width: 100%;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

/* Tall "开始新话题" Button (ONLY visible when expanded) */
.new-topic-btn {
  width: 100% !important;
  height: 48px !important;
  line-height: 48px !important;
  padding: 0 16px !important;
  font-size: 15px !important;
  background-color: #409eff;
  color: white;
  border-radius: 8px !important;
  border: none !important;
  justify-content: center;
}

/* Tall Search Box */
.search-input {
  margin-bottom: 16px;
  width: 100% !important;
  box-sizing: border-box !important;
  height: 44px !important;
}

/* Override Element Plus Input Inner Styles */
:deep(.el-input__wrapper) {
  height: 100% !important;
  padding: 0 12px !important;
  box-sizing: border-box !important;
}
:deep(.el-input__inner) {
  height: 100% !important;
  line-height: 44px !important;
  font-size: 14px !important;
}

/* History Header (Divider + Title) */
.history-header {
  margin: 8px 0 12px;
  width: 100%;
  box-sizing: border-box;
}
.divider {
  height: 1px;
  background-color: #e6e6e6;
  width: 100%;
  margin-bottom: 8px;
}
.title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.clock-icon {
  color: #909399;
  font-size: 16px;
}
.title-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

/* Historic Topics List (ONLY visible when expanded) */
.history-container {
  flex: 1;
  overflow: auto;
  max-height: calc(100vh - 200px);
  width: 100% !important;
  box-sizing: border-box !important;
}
.history-menu {
  border-right: none;
  width: 100% !important;
  box-sizing: border-box !important;
}

/* Topic Item (Ellipsis for long text) */
.topic-item {
  display: flex;
  flex-direction: column;
  width: 100% !important;
  padding: 8px 0;
  box-sizing: border-box;
}
.topic-text {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  width: 100% !important;
}

/* Override Element Plus Menu Styles */
:deep(.el-menu-item) {
  padding: 0 8px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}
</style>