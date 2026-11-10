<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">管理后台</h1>
      <p class="page-subtitle">平台数据统计与管理</p>
    </div>

    <div class="stats-grid">
      <div v-for="(val, key) in statLabels" :key="key" class="card stat-card">
        <div class="stat-value">{{ stats[key] || 0 }}</div>
        <div class="stat-label">{{ val }}</div>
      </div>
    </div>

    <!-- 数据导出 -->
    <div class="card export-section">
      <h2 class="section-title"><span>📥</span> 数据导出报表</h2>
      <p class="export-hint">导出 CSV 格式数据，可用 Excel 打开查看</p>
      <div class="export-grid">
        <button v-for="item in exportTypes" :key="item.type" class="btn btn-outline export-btn" :disabled="exporting" @click="handleExport(item.type)">
          {{ item.icon }} {{ item.label }}
        </button>
      </div>
    </div>

    <div class="admin-actions">
      <router-link to="/admin/users" class="card action-card">
        <span class="action-icon">👥</span><span>用户管理</span>
      </router-link>
      <router-link to="/admin/students" class="card action-card">
        <span class="action-icon">🎓</span><span>学籍库</span>
      </router-link>
      <router-link to="/admin/agent" class="card action-card">
        <span class="action-icon">🤖</span><span>多智能体协作</span>
      </router-link>
      <div class="card action-card" @click="showAnnForm = !showAnnForm">
        <span class="action-icon">📢</span><span>发布公告</span>
      </div>
      <div class="card action-card" @click="showArtForm = !showArtForm">
        <span class="action-icon">📝</span><span>发布文章</span>
      </div>
    </div>

    <div v-if="showAnnForm" class="card" style="margin-top:20px">
      <h2 class="section-title">发布新公告</h2>
      <div class="form-group"><input v-model="annForm.title" class="form-input" placeholder="公告标题" /></div>
      <div class="form-group"><textarea v-model="annForm.content" class="form-textarea" placeholder="公告内容" rows="4"></textarea></div>
      <button class="btn btn-primary" @click="handleCreateAnn">发布</button>
    </div>

    <div v-if="showArtForm" class="card" style="margin-top:20px">
      <h2 class="section-title">发布新文章</h2>
      <div class="form-group"><input v-model="artForm.title" class="form-input" placeholder="文章标题" /></div>
      <div class="form-group"><input v-model="artForm.category" class="form-input" placeholder="分类" /></div>
      <div class="form-group"><textarea v-model="artForm.content" class="form-textarea" placeholder="文章内容（建议450字以上）" rows="8"></textarea></div>
      <button class="btn btn-primary" @click="handleCreateArt">发布</button>
    </div>
  </div>
</template>

<script setup>
/**
 * 管理后台仪表盘 - 含数据导出
 */
import { ref, onMounted } from 'vue'
import { getDashboard, createAnnouncement, createArticle, exportData } from '../../api'

const stats = ref({})
const showAnnForm = ref(false)
const showArtForm = ref(false)
const exporting = ref(false)
const annForm = ref({ title: '', content: '' })
const artForm = ref({ title: '', content: '', category: '心理健康' })

const statLabels = {
  user_count: '总用户数', student_count: '学生数', counselor_count: '咨询师数',
  registry_total: '学籍总数', registry_registered: '已注册学籍', registry_unregistered: '未注册学籍',
  appointment_count: '预约总数', pending_appointments: '待确认预约',
  article_count: '文章数', scale_record_count: '测评记录',
  consultation_count: '活跃咨询', tree_hole_count: '栖心树洞留言', notification_count: '通知总数'
}

const exportTypes = [
  { type: 'users', label: '导出用户', icon: '👥' },
  { type: 'appointments', label: '导出预约', icon: '📅' },
  { type: 'scale_records', label: '导出测评', icon: '📋' },
  { type: 'articles', label: '导出文章', icon: '📖' },
  { type: 'student_registry', label: '导出学籍', icon: '🎓' },
  { type: 'tree_hole', label: '导出栖心树洞', icon: '🕊️' },
]

onMounted(async () => {
  try {
    const res = await getDashboard()
    stats.value = res.data
  } catch (e) { console.error(e) }
})

async function handleExport(type) {
  exporting.value = true
  try {
    await exportData(type)
  } catch (e) { alert(e.message) }
  finally { exporting.value = false }
}

async function handleCreateAnn() {
  try {
    await createAnnouncement(annForm.value)
    alert('公告发布成功')
    annForm.value = { title: '', content: '' }
    showAnnForm.value = false
  } catch (e) { alert(e.message) }
}

async function handleCreateArt() {
  try {
    await createArticle(artForm.value)
    alert('文章发布成功')
    artForm.value = { title: '', content: '', category: '心理健康' }
    showArtForm.value = false
  } catch (e) { alert(e.message) }
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.stat-card { text-align: center; padding: 18px 12px; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--primary); }
.stat-label { font-size: 14px; color: var(--text-muted); margin-top: 4px; }

.export-section { margin-bottom: 24px; padding: 24px; }
.export-hint { font-size: 15px; color: var(--text-muted); margin-bottom: 16px; }
.export-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.export-btn { min-width: 130px; }

.admin-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.action-card {
  text-align: center; padding: 24px;
  cursor: pointer; transition: transform 0.2s; color: inherit;
}
.action-card:hover { transform: translateY(-2px); }
.action-icon { font-size: 34px; display: block; margin-bottom: 8px; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
