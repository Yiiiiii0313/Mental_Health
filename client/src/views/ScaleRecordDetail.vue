<template>
  <div class="record-page">
    <router-link to="/scales" class="back-link">← 返回心理测评</router-link>

    <div v-if="record" class="card result-card" :class="levelClass">
      <div class="result-header">
        <span class="result-badge">{{ record.scale_name }}</span>
        <h2>测评报告</h2>
        <p class="result-meta">测评时间：{{ record.created_at?.substring(0, 16) }}</p>
        <p class="result-summary">{{ record.result_desc }}</p>
      </div>

      <div class="result-score-box">
        <div class="score-item">
          <span class="score-label">总分</span>
          <span class="score-value">{{ record.total_score }}</span>
        </div>
        <div class="score-item">
          <span class="score-label">评估等级</span>
          <span class="score-level">{{ record.result_level }}</span>
        </div>
      </div>

      <div v-if="record.result_analysis" class="result-section">
        <h3 class="section-label">📋 具体分析</h3>
        <p class="section-text">{{ record.result_analysis }}</p>
      </div>

      <div v-if="adviceItems.length" class="result-section advice-section">
        <h3 class="section-label">💡 改善建议</h3>
        <ul class="advice-list">
          <li v-for="(item, i) in adviceItems" :key="i">{{ item }}</li>
        </ul>
      </div>

      <p class="result-disclaimer">* 测评结果仅供参考，不能替代专业心理诊断。如有需要，请预约心理咨询。</p>

      <div class="result-actions">
        <router-link :to="`/scales/${record.scale_id}`" class="btn btn-primary">再次测评</router-link>
        <router-link to="/scales" class="btn btn-outline">返回列表</router-link>
      </div>
    </div>

    <div v-if="loading" class="empty-state card">加载中...</div>
    <div v-else-if="!record" class="empty-state card">记录不存在或无权查看</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getScaleRecord } from '../api'

const route = useRoute()
const record = ref(null)
const loading = ref(true)

const levelClass = computed(() => {
  const level = record.value?.result_level || ''
  if (level.includes('无') || level.includes('较低') || level.includes('适中')) return 'level-good'
  if (level.includes('轻度')) return 'level-mild'
  if (level.includes('中度') || level.includes('较高')) return 'level-moderate'
  return 'level-severe'
})

const adviceItems = computed(() => {
  const text = record.value?.result_advice || ''
  return text.split('\n').map(s => s.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
})

onMounted(async () => {
  try {
    const res = await getScaleRecord(route.params.id)
    record.value = res.data
  } catch (e) {
    record.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.record-page {
  max-width: 720px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 16px;
  color: var(--primary);
  font-size: 16px;
}

.result-card {
  padding: 36px;
  border-top: 4px solid var(--primary);
}

.result-card.level-good { border-top-color: #52c41a; }
.result-card.level-mild { border-top-color: #faad14; }
.result-card.level-moderate { border-top-color: #fa8c16; }
.result-card.level-severe { border-top-color: #f5222d; }

.result-header { text-align: center; margin-bottom: 28px; }

.result-badge {
  display: inline-block;
  background: rgba(61, 139, 158, 0.1);
  color: var(--primary);
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
}

.result-header h2 { font-size: 24px; margin-bottom: 8px; }
.result-meta { font-size: 15px; color: var(--text-muted); margin-bottom: 8px; }
.result-summary { color: var(--text-secondary); font-size: 17px; line-height: 1.6; }

.result-score-box {
  display: flex;
  gap: 20px;
  margin-bottom: 28px;
}

.score-item {
  flex: 1;
  text-align: center;
  padding: 20px;
  background: var(--bg-secondary, #f8fafb);
  border-radius: 12px;
}

.score-label { display: block; font-size: 15px; color: var(--text-muted); margin-bottom: 8px; }
.score-value { font-size: 34px; font-weight: 700; color: var(--primary); }
.score-level { font-size: 20px; font-weight: 600; }

.result-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafcfd;
  border-radius: 12px;
  border-left: 3px solid var(--primary);
}

.advice-section { border-left-color: #52c41a; }

.section-label { font-size: 17px; font-weight: 600; margin-bottom: 12px; }
.section-text { font-size: 17px; line-height: 1.85; text-indent: 2em; }

.advice-list { list-style: none; padding: 0; margin: 0; }

.advice-list li {
  position: relative;
  padding: 8px 0 8px 20px;
  font-size: 16px;
  line-height: 1.7;
  border-bottom: 1px dashed var(--border-light);
}

.advice-list li:last-child { border-bottom: none; }
.advice-list li::before {
  content: '•';
  position: absolute;
  left: 4px;
  color: #52c41a;
  font-weight: bold;
}

.result-disclaimer {
  font-size: 14px;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 24px;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>
