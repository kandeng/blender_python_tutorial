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

  aiAvatar: {
    type: String,
    default: null  // Null means use default icon
  },
  userAvatar: {
    type: String,
    default: null
  },

  chatMessages: {
    type: Array,
    required: true
  },

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
.chat-messages-container {
  width: 100%;
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 20px;
  background-color: #f9f9f9;
  display: flex; /* Add this */
  flex-direction: column; /* Add this */
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  /* Add this to make messages align properly within container */
  display: flex;
  flex-direction: column;
}

.message {
  display: flex;
  margin-bottom: 16px;
  max-width: 70%;
  /* Remove width: 100% to allow proper alignment */
}

.user-message {
  flex-direction: row-reverse;
  /* Align user messages to the right side of the container */
  align-self: flex-end;
  /* Add this to push avatar to far right */
  margin-left: auto;
}

.user-avatar {
  width: 36px;
  height: 36px;
  /* Adjust margins for reversed layout */
  margin: 0 0 0 12px;
  flex-shrink: 0;
}
</style>