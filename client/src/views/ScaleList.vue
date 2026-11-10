<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">心理测评</h1>
      <p class="page-subtitle">通过专业心理量表了解自己的心理状态，测评结果仅供参考，不能替代专业诊断</p>
    </div>

    <div class="scale-grid">
      <div v-for="(scale, i) in scales" :key="scale.id" class="scale-card card">
        <div class="scale-badge" :style="{ background: badgeColors[i % badgeColors.length] }">
          {{ scale.question_count }}题
        </div>
        <h3>{{ scale.name }}</h3>
        <p class="scale-desc">{{ scale.description }}</p>
        <router-link :to="`/scales/${scale.id}`" class="btn btn-primary scale-btn">开始测评</router-link>
      </div>
    </div>

    <div class="card records-card">
      <h2 class="section-title"><span>📊</span> 测评结果趋势</h2>
      <TrendChart :data="trends" />
    </div>

    <div class="card records-card" style="margin-top:24px">
      <h2 class="section-title"><span>📋</span> 我的测评记录</h2>
      <table v-if="records.length" class="table">
        <thead>
          <tr>
            <th>量表</th>
            <th>总分</th>
            <th>结果</th>
            <th>测评时间</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in records"
            :key="r.id"
            class="record-row"
            @click="$router.push(`/scales/records/${r.id}`)"
          >
            <td>{{ r.scale_name }}</td>
            <td><strong>{{ r.total_score }}</strong></td>
            <td><span class="result-tag">{{ r.result_level }}</span></td>
            <td>{{ r.created_at?.substring(0, 16) }} <span class="view-hint">查看 →</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无测评记录，选择上方量表开始第一次测评吧</div>
    </div>
  </div>
</template>

<script setup>
/**
 * 心理量表列表页面
 */
import { ref, onMounted } from 'vue'
import { getScales, getScaleRecords, getScaleTrends } from '../api'
import TrendChart from '../components/TrendChart.vue'

const scales = ref([])
const records = ref([])
const trends = ref([])
const badgeColors = ['#3d8b9e', '#6bc9a0', '#7b9fd4', '#b08bd4']

onMounted(async () => {
  try {
    const [scaleRes, recordRes, trendRes] = await Promise.all([
      getScales(),
      getScaleRecords({ page: 1, page_size: 10 }),
      getScaleTrends()
    ])
    scales.value = scaleRes.data
    records.value = recordRes.data.list
    trends.value = trendRes.data
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.scale-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.scale-card {
  position: relative;
  padding-top: 32px;
}

.scale-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 4px 12px;
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.scale-card h3 {
  font-size: 19px;
  font-weight: 600;
  margin-bottom: 10px;
  padding-right: 60px;
}

.scale-desc {
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.7;
  margin-bottom: 20px;
  min-height: 48px;
}

.scale-btn { width: 100%; }

.records-card { padding: 28px; }

.result-tag {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(61, 139, 158, 0.1);
  color: var(--primary);
  border-radius: 6px;
  font-size: 15px;
}

.record-row {
  cursor: pointer;
  transition: var(--transition);
}

.record-row:hover {
  background: rgba(61, 139, 158, 0.05);
}

.view-hint {
  color: var(--primary);
  font-size: 14px;
  opacity: 0;
  transition: var(--transition);
}

.record-row:hover .view-hint {
  opacity: 1;
}

@media (max-width: 900px) {
  .scale-grid { grid-template-columns: 1fr; }
}
</style>
