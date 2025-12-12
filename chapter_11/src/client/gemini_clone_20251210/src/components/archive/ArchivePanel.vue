<!-- Archive tab content -->
<template>
  <div class="archive-panel">
    <el-table :data="archiveItems" border style="width: 100%">
      <el-table-column prop="title" label="Title" min-width="200"></el-table-column>
      <el-table-column prop="date" label="Created Date" width="180"></el-table-column>
      <el-table-column prop="type" label="Type" width="100"></el-table-column>
      <el-table-column prop="actions" label="Actions" width="150">
        <template #default>
          <el-button type="primary" size="small" icon="Edit"></el-button>
          <el-button type="danger" size="small" icon="Delete"></el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const archiveItems = ref([
  { title: 'Project Proposal', date: '2025-01-10', type: 'Document' },
  { title: 'Client Meeting Notes', date: '2025-01-08', type: 'Notes' },
  { title: 'Design Mockups', date: '2025-01-05', type: 'Images' },
  { title: 'Audio Recording', date: '2025-01-03', type: 'Audio' },
  { title: 'Video Presentation', date: '2025-01-01', type: 'Video' }
])
</script>

<style scoped>
.archive-panel {
  padding: 20px;
}
</style>