<template>
  <div>
    <h1 class="page-title">{{ scale?.name || '心理测评' }}</h1>

    <!-- 测评进行中 -->
    <div v-if="!result && scale" class="card">
      <p style="color:var(--text-secondary);margin-bottom:20px">{{ scale.description }}</p>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <p class="progress-text">第 {{ currentIndex + 1 }} / {{ scale.questions.length }} 题</p>

      <div v-if="currentQuestion" :key="currentQuestion.id" class="question-block">
        <h3 class="question-text">{{ currentQuestion.question_text }}</h3>
        <div class="options">
          <label
            v-for="(opt, idx) in currentQuestion.options_json"
            :key="currentQuestion.id + '-' + idx"
            class="option-item"
            :class="{ selected: answers[currentIndex]?.answer_score === opt.score }"
          >
            <input
              type="radio"
              :name="'q' + currentQuestion.id"
              :value="opt.score"
              :checked="answers[currentIndex]?.answer_score === opt.score"
              @change="selectAnswer(opt.score)"
            />
            {{ opt.label }}
          </label>
        </div>
      </div>

      <div class="nav-buttons">
        <button class="btn btn-outline" :disabled="currentIndex === 0" @click="currentIndex--">上一题</button>
        <button
          v-if="currentIndex < scale.questions.length - 1"
          class="btn btn-primary"
          :disabled="!answers[currentIndex]"
          @click="currentIndex++"
        >下一题</button>
        <button
          v-else
          class="btn btn-primary"
          :disabled="!allAnswered || submitting"
          @click="handleSubmit"
        >{{ submitting ? '提交中...' : '提交测评' }}</button>
      </div>
    </div>

    <!-- 测评结果 -->
    <div v-if="result" class="card result-card" :class="levelClass">
      <div class="result-header">
        <span class="result-badge">{{ result.scale_name }}</span>
        <h2>测评完成</h2>
        <p class="result-summary">{{ result.result_desc }}</p>
      </div>

      <div class="result-score-box">
        <div class="score-item">
          <span class="score-label">总分</span>
          <span class="score-value">{{ result.total_score }}</span>
        </div>
        <div class="score-item">
          <span class="score-label">评估等级</span>
          <span class="score-level">{{ result.result_level }}</span>
        </div>
      </div>

      <div v-if="result.result_analysis" class="result-section">
        <h3 class="section-label">📋 具体分析</h3>
        <p class="section-text">{{ result.result_analysis }}</p>
      </div>

      <div v-if="adviceItems.length" class="result-section advice-section">
        <h3 class="section-label">💡 改善建议</h3>
        <ul class="advice-list">
          <li v-for="(item, i) in adviceItems" :key="i">{{ item }}</li>
        </ul>
      </div>

      <p class="result-disclaimer">* 测评结果仅供参考，不能替代专业心理诊断。如有需要，请预约心理咨询。</p>

      <div class="result-actions">
        <router-link to="/scales" class="btn btn-primary">返回量表列表</router-link>
        <router-link v-if="result.record_id" :to="`/scales/records/${result.record_id}`" class="btn btn-outline">查看报告详情</router-link>
      </div>
    </div>

    <div v-if="errorMsg" class="alert alert-error" style="margin-top:16px">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
/**
 * 心理量表测评页面
 * 逐题作答并提交获取评估结果
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getScale, submitScale } from '../api'

const route = useRoute()
const scale = ref(null)
const currentIndex = ref(0)
const answers = ref([])
const result = ref(null)
const submitting = ref(false)
const errorMsg = ref('')

const currentQuestion = computed(() => scale.value?.questions?.[currentIndex.value])
const progressPercent = computed(() => {
  if (!scale.value) return 0
  return ((currentIndex.value + 1) / scale.value.questions.length) * 100
})
const allAnswered = computed(() => {
  if (!scale.value?.questions?.length) return false
  return scale.value.questions.every((q, idx) => {
    const a = answers.value[idx]
    return a && a.question_id === q.id && a.answer_score !== undefined && a.answer_score !== null
  })
})

const levelClass = computed(() => {
  const level = result.value?.result_level || ''
  if (level.includes('无') || level.includes('较低') || level.includes('适中')) return 'level-good'
  if (level.includes('轻度')) return 'level-mild'
  if (level.includes('中度') || level.includes('较高')) return 'level-moderate'
  return 'level-severe'
})

const adviceItems = computed(() => {
  const text = result.value?.result_advice || ''
  return text.split('\n').map(s => s.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
})

onMounted(async () => {
  try {
    const res = await getScale(route.params.id)
    scale.value = res.data
    answers.value = new Array(res.data.questions.length)
  } catch (e) {
    errorMsg.value = e.message
  }
})

/** 选择答案 */
function selectAnswer(score) {
  const q = currentQuestion.value
  answers.value[currentIndex.value] = {
    question_id: q.id,
    answer_score: score
  }
}

/** 提交测评 */
async function handleSubmit() {
  submitting.value = true
  errorMsg.value = ''
  try {
    const payload = scale.value.questions.map((q, idx) => answers.value[idx]).filter(Boolean)
    const res = await submitScale(route.params.id, { answers: payload })
    result.value = res.data
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.progress-bar {
  height: 6px;
  background: #e8ecef;
  border-radius: 3px;
  margin-bottom: 8px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a90a4, #7ec8a0);
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-text { font-size: 15px; color: var(--text-muted); margin-bottom: 24px; }

.question-text { font-size: 20px; margin-bottom: 20px; line-height: 1.5; }

.options { display: flex; flex-direction: column; gap: 10px; }
.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border: 1px solid #e8ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 17px;
}
.option-item:hover { border-color: #4a90a4; background: #f0f8fa; }
.option-item.selected { border-color: #4a90a4; background: #e8f4f8; }
.option-item input { accent-color: #4a90a4; }

.nav-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
}

.result-card {
  max-width: 720px;
  margin: 0 auto;
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

.score-label { display: block; font-size: 15px; color: var(--text-muted, var(--text-muted)); margin-bottom: 8px; }
.score-value { font-size: 34px; font-weight: 700; color: var(--primary); }
.score-level { font-size: 20px; font-weight: 600; color: var(--text); }

.result-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafcfd;
  border-radius: 12px;
  border-left: 3px solid var(--primary);
}

.advice-section { border-left-color: #52c41a; }

.section-label { font-size: 17px; font-weight: 600; margin-bottom: 12px; }
.section-text { font-size: 17px; line-height: 1.85; color: var(--text); text-indent: 2em; }

.advice-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.advice-list li {
  position: relative;
  padding: 8px 0 8px 20px;
  font-size: 16px;
  line-height: 1.7;
  color: var(--text);
  border-bottom: 1px dashed var(--border-light, #e8ecef);
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
  color: var(--text-muted, var(--text-muted));
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
