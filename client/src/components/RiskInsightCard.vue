<template>
  <div class="risk-insight card">
    <div class="insight-header">
      <h2 class="section-title"><span>🧠</span> 心理健康洞察</h2>
      <span class="coverage" v-if="data?.has_data">数据覆盖 {{ data.data_coverage }}%</span>
    </div>

    <div v-if="loading" class="loading-state">分析中...</div>

    <template v-else-if="data?.has_data">
      <div class="insight-body">
        <div class="score-panel" :style="{ '--risk-color': data.risk_color }">
          <div class="score-ring">
            <svg viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" class="ring-bg" />
              <circle
                cx="60" cy="60" r="52"
                class="ring-fill"
                :stroke-dasharray="`${data.risk_score * 3.27} 327`"
              />
            </svg>
            <div class="score-center">
              <strong>{{ data.risk_score }}</strong>
              <span>风险指数</span>
            </div>
          </div>
          <div class="score-info">
            <span class="risk-badge" :style="{ background: data.risk_color + '22', color: data.risk_color }">
              {{ data.risk_level }}
            </span>
            <p class="risk-label">{{ data.risk_label }}</p>
            <p class="trend-summary">
              <span class="trend-icon">{{ trendIcon }}</span>
              {{ data.trend_summary }}
            </p>
          </div>
        </div>

        <div class="factors-panel">
          <h3>评估因子</h3>
          <div v-for="f in data.factors" :key="f.key" class="factor-item">
            <div class="factor-head">
              <span>{{ f.name }}</span>
              <span class="factor-score">{{ f.score }} / {{ f.max_score }}</span>
            </div>
            <div class="factor-bar-bg">
              <div class="factor-bar-fill" :style="{ width: f.risk_percent + '%' }"></div>
            </div>
            <div v-if="f.trend" class="factor-trend" :class="f.trend_arrow">
              {{ trendArrow(f.trend_arrow) }} {{ f.trend }}
              <span v-if="f.predicted_score !== undefined"> · 预测 {{ f.predicted_score }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="data.predictions?.length" class="predictions">
        <h3>趋势预测</h3>
        <div class="prediction-grid">
          <div v-for="p in data.predictions" :key="p.name" class="prediction-card">
            <span class="pred-name">{{ p.name }}</span>
            <div class="pred-values">
              <span>当前 <strong>{{ p.current }}</strong></span>
              <span class="pred-arrow" :class="p.trend_arrow">→</span>
              <span>预测 <strong>{{ p.predicted }}</strong></span>
            </div>
            <span class="pred-trend" :class="p.trend_arrow">{{ p.trend }}</span>
          </div>
        </div>
      </div>

      <div v-if="data.suggestions?.length" class="suggestions">
        <h3>建议</h3>
        <ul>
          <li v-for="(s, i) in data.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>
    </template>

    <div v-else class="empty-insight">
      <p>{{ data?.message || '暂无评估数据' }}</p>
      <ul v-if="data?.suggestions?.length">
        <li v-for="(s, i) in data.suggestions" :key="i">{{ s }}</li>
      </ul>
      <router-link to="/scales" class="btn btn-primary">去测评</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getRiskInsight } from '../api'

const data = ref(null)
const loading = ref(true)

const trendIcon = computed(() => {
  const t = data.value?.overall_trend
  if (t === 'improving') return '📈'
  if (t === 'declining') return '📉'
  if (t === 'watch') return '👀'
  return '➡️'
})

function trendArrow(arrow) {
  if (arrow === 'up') return '↑'
  if (arrow === 'down') return '↓'
  return '→'
}

onMounted(async () => {
  try {
    const res = await getRiskInsight()
    data.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.risk-insight {
  padding: 28px;
  margin-bottom: 24px;
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.coverage {
  font-size: 14px;
  color: var(--text-muted);
}

.loading-state, .empty-insight {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary);
}

.empty-insight ul {
  text-align: left;
  max-width: 360px;
  margin: 12px auto 20px;
  padding-left: 20px;
  font-size: 16px;
  line-height: 1.8;
}

.insight-body {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 28px;
  margin-bottom: 24px;
}

.score-panel {
  display: flex;
  gap: 20px;
  align-items: center;
}

.score-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.score-ring svg {
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #eef2f6;
  stroke-width: 10;
}

.ring-fill {
  fill: none;
  stroke: var(--risk-color, var(--primary));
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.score-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-center strong {
  font-size: 30px;
  color: var(--risk-color, var(--primary));
  line-height: 1;
}

.score-center span {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}

.risk-label {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 8px;
}

.trend-summary {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.factors-panel h3, .predictions h3, .suggestions h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text);
}

.factor-item {
  margin-bottom: 14px;
}

.factor-head {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  margin-bottom: 6px;
}

.factor-score {
  color: var(--text-muted);
}

.factor-bar-bg {
  height: 8px;
  background: #eef2f6;
  border-radius: 4px;
  overflow: hidden;
}

.factor-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 4px;
  transition: width 0.5s ease;
}

.factor-trend {
  font-size: 14px;
  margin-top: 4px;
  color: var(--text-muted);
}

.factor-trend.up { color: #fa8c16; }
.factor-trend.down { color: #52c41a; }

.predictions {
  margin-bottom: 20px;
}

.prediction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.prediction-card {
  padding: 14px;
  background: #f8fafb;
  border-radius: 10px;
  border: 1px solid var(--border-light);
}

.pred-name {
  font-size: 15px;
  font-weight: 600;
  display: block;
  margin-bottom: 8px;
}

.pred-values {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.pred-arrow.up { color: #fa8c16; }
.pred-arrow.down { color: #52c41a; }

.pred-trend {
  font-size: 13px;
  color: var(--text-muted);
}

.pred-trend.up { color: #fa8c16; }
.pred-trend.down { color: #52c41a; }

.suggestions ul {
  padding-left: 20px;
  font-size: 16px;
  line-height: 1.9;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .insight-body {
    grid-template-columns: 1fr;
  }
}
</style>
