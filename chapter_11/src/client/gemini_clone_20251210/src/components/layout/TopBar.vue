<!-- Top bar (tabs + user profile) -->
<template>
  <el-header class="top-bar">
    <!-- ✅ Use v-model on LOCAL reactive variable (not prop) -->
    <el-tabs
      v-model="localActiveTab"
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
    <div class="user-profile" @click="showLoginModal = true">
      <el-avatar :src="userAvatar" class="avatar" icon="User"></el-avatar>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from 'vue'

// ✅ Define read-only props (from parent App.vue)
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

// ✅ Define emits to communicate with parent
const emit = defineEmits(['tab-change', 'open-login'])

// ✅ Local reactive variable (mirrors parent's activeTab prop)
const localActiveTab = ref(props.activeTab)
const showLoginModal = ref(false)

// ✅ Sync parent prop changes to local variable (if parent updates activeTab)
watch(
  () => props.activeTab,
  (newValue) => {
    localActiveTab.value = newValue
  },
  { immediate: true } // Sync initial value
)

// ✅ Handle tab change (emit to parent)
const handleTabChange = (tab) => {
  localActiveTab.value = tab // Update local state
  emit('tab-change', tab)    // Forward to parent
}

// ✅ Emit login modal open event
watch(showLoginModal, (val) => {
  if (val) emit('open-login')
})
</script>

<style scoped>
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
</style>
