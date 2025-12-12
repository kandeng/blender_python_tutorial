<!-- Login/register modal -->
<template>
  <!-- ✅ Replace v-model with model-value + update:model-value -->
  <el-dialog
    :model-value="showModal"  
    @update:model-value="emit('update:showModal', $event)" 
    title="User Authentication"
    width="400px"
    :close-on-click-modal="false"
  >
    <el-tabs v-model="authTab" type="card">
      <el-tab-pane name="login" label="Login">
        <el-form :model="loginForm" label-width="80px">
          <el-form-item label="Email">
            <el-input v-model="loginForm.email" type="email"></el-input>
          </el-form-item>
          <el-form-item label="Password">
            <el-input v-model="loginForm.password" type="password"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleLogin">Login</el-button>
            <el-button @click="handleCancel">Cancel</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane name="register" label="Register">
        <el-form :model="registerForm" label-width="80px">
          <el-form-item label="Name">
            <el-input v-model="registerForm.name"></el-input>
          </el-form-item>
          <el-form-item label="Email">
            <el-input v-model="registerForm.email" type="email"></el-input>
          </el-form-item>
          <el-form-item label="Password">
            <el-input v-model="registerForm.password" type="password"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleRegister">Register</el-button>
            <el-button @click="handleCancel">Cancel</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// ✅ Define props (showModal is read-only)
const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  }
})

// ✅ Define emits for parent communication
const emit = defineEmits(['update:showModal', 'login-success'])

// Local state
const authTab = ref('login')
const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ name: '', email: '', password: '' })

// Handle login (emit success + close modal)
const handleLogin = () => {
  ElMessage.success('Login successful!')
  emit('login-success', 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
  emit('update:showModal', false) // Close modal
}

// Handle register (switch to login tab)
const handleRegister = () => {
  ElMessage.success('Registration successful! Please login.')
  authTab.value = 'login'
}

// Handle cancel (close modal)
const handleCancel = () => {
  emit('update:showModal', false)
}
</script>
