<!-- Gallery tab content with Pinterest-like masonry layout with varying image heights and staggered arrangement -->
<template>
  <div class="gallery-panel">
    <div class="masonry-grid">
      <div class="masonry-item" v-for="(image, index) in galleryImages" :key="index">
        <el-card class="gallery-card">
          <el-image 
            :src="image.url" 
            fit="cover" 
            class="gallery-image" 
            :preview-src-list="previewUrls"
            :style="{ height: `${image.height}px` }"
          ></el-image>
          <div class="gallery-card-footer"><span>{{ image.title }}</span></div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Updated with varying image heights to create Pinterest-like staggered effect
const galleryImages = ref([
  { url: 'https://picsum.photos/800/1000?random=1', title: 'Landscape Photo 1', height: 350 },
  { url: 'https://picsum.photos/800/600?random=2', title: 'Portrait Photo 2', height: 250 },
  { url: 'https://picsum.photos/800/800?random=3', title: 'Nature Photo 3', height: 300 },
  { url: 'https://picsum.photos/800/1200?random=4', title: 'City Photo 4', height: 400 },
  { url: 'https://picsum.photos/800/700?random=5', title: 'Animal Photo 5', height: 280 },
  { url: 'https://picsum.photos/800/900?random=6', title: 'Architecture Photo 6', height: 320 },
  { url: 'https://picsum.photos/800/500?random=7', title: 'Mountain Photo 7', height: 220 },
  { url: 'https://picsum.photos/800/1100?random=8', title: 'Beach Photo 8', height: 380 },
  { url: 'https://picsum.photos/800/650?random=9', title: 'Forest Photo 9', height: 260 }
])

const previewUrls = computed(() => {
  return galleryImages.value.map(img => img.url)
})
</script>

<style scoped>
.gallery-panel {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Masonry grid layout */
.masonry-grid {
  column-count: 1;
  column-gap: 20px;
}

@media (min-width: 640px) {
  .masonry-grid { column-count: 2; }
}

@media (min-width: 768px) {
  .masonry-grid { column-count: 3; }
}

@media (min-width: 1024px) {
  .masonry-grid { column-count: 4; }
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 20px;
}

.gallery-card {
  border: none;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: transform 0.2s ease;
}

.gallery-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.gallery-image {
  width: 100%;
  border-radius: 12px 12px 0 0;
}

.gallery-card-footer {
  padding: 12px 15px;
  background: #fff;
  font-size: 14px;
  color: #333;
}
</style>