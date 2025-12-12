<!--  Sidebar (navigation) -->
<template>
  <el-aside
    :width="isSidebarCollapsed ? '64px' : '240px'"
    class="sidebar"
    transition="width-collapse"
  >
    <el-button
      @click="isSidebarCollapsed = !isSidebarCollapsed"
      class="collapse-btn"
      circle
      icon="Menu"
    ></el-button>
    <el-menu
      default-active="1"
      class="sidebar-menu"
      :collapse="isSidebarCollapsed"
      collapse-transition
      @select="handleMenuSelect"
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
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['menu-select'])
const isSidebarCollapsed = ref(false)

const handleMenuSelect = (index) => {
  const tabMap = {
    '1': 'chatbot',
    '2': 'gallery',
    '3': 'archive'
  }
  if (tabMap[index]) {
    emit('menu-select', tabMap[index])
  }
}
</script>

<style scoped>
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
</style>