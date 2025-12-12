<!-- Chat message list + file previews -->
<template>
  <div class="chat-messages" ref="localMessagesContainer">
    <MessageItem
      v-for="(msg, index) in chatMessages"
      :key="index"
      :msg="msg"
      :ai-avatar="aiAvatar"
      :user-avatar="userAvatar"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import MessageItem from './MessageItem.vue'

const props = defineProps({
  chatMessages: {
    type: Array,
    required: true
  },
  aiAvatar: {
    type: String,
    required: true
  },
  userAvatar: {
    type: String,
    required: true
  },
  // ✅ Fix 1: Allow null/undefined (or make optional)
  messagesContainer: {
    type: Object,
    default: null, // Allow null by default
    required: false // Remove "required: true" (or keep and allow null)
  }
})

// ✅ Fix 2: Use a LOCAL ref for the container (more reliable than parent-passed prop)
const localMessagesContainer = ref(null)

// Auto-scroll logic (guard against null)
watch(props.chatMessages, () => {
  setTimeout(() => {
    // Use local container first (fallback to parent-passed)
    const container = localMessagesContainer.value || props.messagesContainer
    if (container) { // Guard clause: only scroll if container exists
      container.scrollTop = container.scrollHeight
    }
  }, 0)
})

// Expose local container for parent access (if needed)
defineExpose({
  messagesContainer: localMessagesContainer
})
</script>

<style scoped>
.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>