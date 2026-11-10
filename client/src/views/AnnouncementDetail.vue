<template>
  <div class="announcement-page">
    <router-link to="/home" class="back-link">← 返回首页</router-link>

    <article v-if="item" class="announcement-detail card">
      <header class="detail-header">
        <span class="ann-badge">📢 平台公告</span>
        <h1>{{ item.title }}</h1>
        <div class="detail-meta">
          <span>发布者：{{ item.publisher_name || '管理员' }}</span>
          <span>发布时间：{{ item.created_at?.substring(0, 16) }}</span>
        </div>
      </header>
      <div class="detail-content">
        <p v-for="(para, i) in paragraphs" :key="i">{{ para }}</p>
      </div>
    </article>

    <div v-if="loading" class="empty-state card">加载中...</div>
    <div v-else-if="!item" class="empty-state card">公告不存在或已下架</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getAnnouncement } from '../api'

const route = useRoute()
const item = ref(null)
const loading = ref(true)

const paragraphs = computed(() => {
  if (!item.value?.content) return []
  return item.value.content.split('\n').filter(p => p.trim())
})

onMounted(async () => {
  try {
    const res = await getAnnouncement(route.params.id)
    item.value = res.data
  } catch (e) {
    item.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.announcement-page {
  max-width: 800px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 16px;
  color: var(--primary);
  font-size: 16px;
}

.announcement-detail {
  padding: 32px;
}

.ann-badge {
  display: inline-block;
  background: #e8f4f8;
  color: var(--primary);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.detail-header h1 {
  font-size: 26px;
  line-height: 1.4;
  margin-bottom: 12px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 15px;
  color: var(--text-muted);
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

.detail-content {
  padding-top: 24px;
}

.detail-content p {
  font-size: 17px;
  line-height: 1.9;
  color: var(--text);
  margin-bottom: 16px;
  text-indent: 2em;
}
</style>
