import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css' 

const app = createApp(App)

// ✅ Register all Element Plus icons globally (as components)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, {
  // ✅ Disable auto-inlining of icons (uses SVG sprites instead)
  icon: {
    default: 'svg', // Force SVG sprite usage
    size: 'default'
  }
})

app.mount('#app')