/**
 * 测评结果趋势折线图组件（纯 SVG 实现）
 */
<template>
  <div class="trend-chart">
    <div v-if="!data.length" class="chart-empty">暂无足够数据绘制趋势图，完成多次测评后可见</div>
    <div v-for="group in data" :key="group.scale_id" class="chart-group">
      <h4>{{ group.scale_name }}</h4>
      <svg :viewBox="`0 0 ${width} ${height}`" class="chart-svg">
        <!-- 网格线 -->
        <line v-for="i in 4" :key="'g'+i"
          :x1="padding" :y1="padding + (chartH / 4) * i"
          :x2="width - padding" :y2="padding + (chartH / 4) * i"
          stroke="#e8ecef" stroke-width="1"
        />
        <!-- 折线 -->
        <polyline
          v-if="group.records.length > 1"
          :points="getPoints(group.records)"
          fill="none" stroke="#3d8b9e" stroke-width="2.5" stroke-linejoin="round"
        />
        <!-- 数据点 -->
        <circle
          v-for="(pt, i) in getPointCoords(group.records)"
          :key="i"
          :cx="pt.x" :cy="pt.y" r="5"
          fill="#3d8b9e" stroke="#fff" stroke-width="2"
        />
        <!-- 分数标签 -->
        <text
          v-for="(pt, i) in getPointCoords(group.records)"
          :key="'t'+i"
          :x="pt.x" :y="pt.y - 12"
          text-anchor="middle" font-size="11" fill="#3d8b9e" font-weight="600"
        >{{ pt.score }}</text>
      </svg>
      <div class="chart-labels">
        <span v-for="(r, i) in group.records" :key="i">{{ r.date }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * SVG 折线图，展示量表测评分数变化趋势
 */
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const width = 500
const height = 200
const padding = 40
const chartH = height - padding * 2

/** 计算折线坐标点字符串 */
function getPoints(records) {
  return getPointCoords(records).map(p => `${p.x},${p.y}`).join(' ')
}

/** 将分数映射为 SVG 坐标 */
function getPointCoords(records) {
  if (!records.length) return []
  const maxScore = Math.max(...records.map(r => r.score), 1)
  const step = records.length > 1 ? (width - padding * 2) / (records.length - 1) : 0
  return records.map((r, i) => ({
    x: padding + step * i,
    y: padding + chartH - (r.score / maxScore) * chartH,
    score: r.score
  }))
}
</script>

<style scoped>
.trend-chart { width: 100%; }
.chart-group { margin-bottom: 24px; }
.chart-group h4 {
  font-size: 16px;
  color: var(--primary);
  margin-bottom: 8px;
}
.chart-svg {
  width: 100%;
  max-width: 500px;
  height: auto;
}
.chart-labels {
  display: flex;
  justify-content: space-between;
  max-width: 500px;
  padding: 0 30px;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
.chart-empty {
  text-align: center;
  padding: 30px;
  color: var(--text-muted);
  font-size: 16px;
}
</style>
