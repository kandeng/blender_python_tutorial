<!-- Gallery tab content -->
<template>
  <div class="gallery-panel">
    <el-row :gutter="20">
      <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="(image, index) in galleryImages" :key="index">
        <el-card class="gallery-card">
          <el-image :src="image.url" fit="cover" class="gallery-image" :preview-src-list="previewUrls"></el-image>
          <div class="gallery-card-footer"><span>{{ image.title }}</span></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const galleryImages = ref([
  { url: 'https://picsum.photos/800/600?random=1', title: 'Landscape Photo 1' },
  { url: 'https://picsum.photos/800/600?random=2', title: 'Portrait Photo 2' },
  { url: 'https://picsum.photos/800/600?random=3', title: 'Nature Photo 3' },
  { url: 'https://picsum.photos/800/600?random=4', title: 'City Photo 4' },
  { url: 'https://picsum.photos/800/600?random=5', title: 'Animal Photo 5' },
  { url: 'https://picsum.photos/800/600?random=6', title: 'Architecture Photo 6' }
])

const previewUrls = computed(() => {
  return galleryImages.value.map(img => img.url)
})
</script>

<style scoped>
.gallery-panel {
  padding: 20px;
}

.gallery-card {
  height: 250px;
  margin-bottom: 20px;
}

.gallery-image {
  height: 200px;
  width: 100%;
}

.gallery-card-footer {
  text-align: center;
  padding: 5px;
}
</style>