<template>
  <div class="agent-page">
    <div class="page-header">
      <div>
        <router-link to="/admin" class="back-link">← 返回管理后台</router-link>
        <h1 class="page-title">多智能体协作</h1>
        <p class="page-subtitle">
          基于 LangChain + LangGraph：数据获取 → 清洗 → 分析 → 可视化 → 报告生成
        </p>
      </div>
    </div>

    <div class="card pipeline-card">
      <h2 class="section-title"><span>🔗</span> 协作流水线</h2>
      <div class="pipeline">
        <div v-for="(p, idx) in pipeline" :key="p.id" class="pipe-item">
          <div class="pipe-dot">{{ idx + 1 }}</div>
          <div>
            <strong>{{ p.name }}</strong>
            <p>{{ p.desc }}</p>
          </div>
        </div>
      </div>
      <p class="engine-tag">引擎：{{ engine }}</p>
    </div>

    <div class="card config-card">
      <h2 class="section-title"><span>⚙️</span> 任务配置</h2>
      <div class="form-group">
        <label>报告主题</label>
        <input
          v-model="topic"
          class="form-input"
          placeholder="例如：本周心理健康运营数据分析报告"
        />
      </div>
      <div class="form-group">
        <label>选择数据集</label>
        <div class="dataset-grid">
          <label v-for="d in datasets" :key="d.key" class="dataset-item">
            <input v-model="selected" type="checkbox" :value="d.key" />
            <span>{{ d.label }}</span>
          </label>
        </div>
      </div>
      <button class="btn btn-primary run-btn" :disabled="running || !selected.length" @click="runAgent">
        {{ running ? '多智能体协作执行中…' : '启动多智能体协作' }}
      </button>
      <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
    </div>

    <div v-if="result || running" class="card steps-card">
      <h2 class="section-title"><span>📡</span> 执行进度</h2>
      <div v-if="running && !result?.steps?.length" class="loading-hint">正在调度 Agent…</div>
      <ul class="step-list">
        <li v-for="(s, i) in result?.steps || []" :key="i" :class="['step', s.status]">
          <span class="step-agent">{{ s.agent }}</span>
          <span class="step-status">{{ statusLabel(s.status) }}</span>
          <span class="step-msg">{{ s.message }}</span>
          <span class="step-time">{{ s.at }}</span>
        </li>
      </ul>
    </div>

    <div v-if="result?.charts?.length" class="card charts-card">
      <h2 class="section-title"><span>📊</span> 可视化结果</h2>
      <div class="charts-grid">
        <figure v-for="c in result.charts" :key="c.url" class="chart-item">
          <img :src="c.url" :alt="c.title" />
          <figcaption>{{ c.title }}</figcaption>
        </figure>
      </div>
    </div>

    <div v-if="result?.report_md" class="card report-card">
      <div class="report-head">
        <h2 class="section-title"><span>📄</span> 分析报告</h2>
        <button class="btn btn-outline btn-sm" @click="copyReport">复制 Markdown</button>
      </div>
      <pre class="report-body">{{ result.report_md }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAgentDatasets, runAgentReport } from '../../api'

const datasets = ref([])
const pipeline = ref([])
const engine = ref('LangChain + LangGraph')
const selected = ref([])
const topic = ref('心屿平台心理健康运营数据分析报告')
const running = ref(false)
const result = ref(null)
const errorMsg = ref('')

function statusLabel(s) {
  return { running: '进行中', done: '完成', warn: '降级', error: '失败' }[s] || s
}

onMounted(async () => {
  try {
    const res = await getAgentDatasets()
    datasets.value = res.data.datasets || []
    pipeline.value = res.data.pipeline || []
    engine.value = res.data.engine || engine.value
    selected.value = datasets.value.map(d => d.key)
  } catch (e) {
    errorMsg.value = e.message
  }
})

async function runAgent() {
  running.value = true
  errorMsg.value = ''
  result.value = null
  try {
    const res = await runAgentReport({
      topic: topic.value,
      datasets: selected.value,
    })
    result.value = res.data
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    running.value = false
  }
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(result.value?.report_md || '')
    alert('报告已复制')
  } catch {
    alert('复制失败，请手动选择文本')
  }
}
</script>

<style scoped>
.back-link {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--primary);
  text-decoration: none;
  font-size: 15px;
}

.pipeline-card, .config-card, .steps-card, .charts-card, .report-card {
  margin-bottom: 20px;
}

.pipeline {
  display: grid;
  gap: 12px;
}

.pipe-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(69, 106, 93, 0.06);
}

.pipe-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.pipe-item p {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}

.engine-tag {
  margin-top: 14px;
  font-size: 13px;
  color: var(--text-muted);
}

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.dataset-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.7);
}

.run-btn {
  margin-top: 8px;
  min-width: 200px;
}

.step-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step {
  display: grid;
  grid-template-columns: 140px 64px 1fr auto;
  gap: 10px;
  align-items: start;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f7faf8;
  font-size: 14px;
}

.step.done { border-left: 3px solid var(--success, #3cb371); }
.step.warn { border-left: 3px solid var(--warning, #f0a030); }
.step.error { border-left: 3px solid var(--danger, #e85d5d); }
.step.running { border-left: 3px solid var(--primary); }

.step-agent { font-weight: 600; color: var(--primary); }
.step-status { color: var(--text-secondary); }
.step-msg { color: var(--text); word-break: break-word; }
.step-time { color: var(--text-muted); white-space: nowrap; font-size: 12px; }

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.chart-item {
  margin: 0;
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  overflow: hidden;
}

.chart-item img {
  width: 100%;
  display: block;
  background: #fafafa;
}

.chart-item figcaption {
  padding: 10px 12px;
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
}

.report-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.report-body {
  white-space: pre-wrap;
  word-break: break-word;
  background: #f8fafb;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  max-height: 640px;
  overflow: auto;
  margin: 0;
}

.loading-hint {
  color: var(--text-muted);
  margin-bottom: 8px;
}

.btn-sm {
  padding: 6px 14px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .step {
    grid-template-columns: 1fr;
  }
}
</style>
