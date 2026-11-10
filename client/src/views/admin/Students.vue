<template>
  <div>
    <div class="page-header-row">
      <div>
        <h1 class="page-title">学籍库管理</h1>
        <p class="page-subtitle">查看全校学生名册及平台注册状态</p>
      </div>
      <router-link to="/admin" class="btn btn-outline">返回后台</router-link>
    </div>

    <div class="stats-row">
      <div class="card stat-card">
        <strong>{{ summary.total }}</strong>
        <span>学籍总数</span>
      </div>
      <div class="card stat-card registered">
        <strong>{{ summary.registered }}</strong>
        <span>已注册</span>
      </div>
      <div class="card stat-card unregistered">
        <strong>{{ summary.unregistered }}</strong>
        <span>未注册</span>
      </div>
    </div>

    <div class="filter-bar card">
      <input
        v-model="keyword"
        class="form-input search-input"
        placeholder="搜索学号或姓名..."
        @keyup.enter="loadData(1)"
      />
      <select v-model="registeredFilter" class="form-select" @change="loadData(1)">
        <option value="">全部状态</option>
        <option value="1">已注册</option>
        <option value="0">未注册</option>
      </select>
      <button class="btn btn-primary" @click="loadData(1)">搜索</button>
      <button class="btn btn-primary" @click="showForm = true">添加学生</button>
      <button class="btn btn-outline" :disabled="exporting" @click="handleExport">导出学籍</button>
    </div>

    <!-- 添加学生弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="card modal-content">
        <h2 class="section-title">添加学生信息</h2>
        <div class="form-group">
          <label>学号 *</label>
          <input v-model="form.student_no" class="form-input" placeholder="如 20250101001" />
        </div>
        <div class="form-group">
          <label>姓名 *</label>
          <input v-model="form.real_name" class="form-input" placeholder="真实姓名" />
        </div>
        <div class="form-group">
          <label>院系</label>
          <input v-model="form.department" class="form-input" placeholder="如 计算机学院" />
        </div>
        <div class="form-group">
          <label>班级</label>
          <input v-model="form.class_name" class="form-input" placeholder="如 计科2501" />
        </div>
        <div class="form-group">
          <label>性别</label>
          <select v-model="form.gender" class="form-select">
            <option :value="0">未知</option>
            <option :value="1">男</option>
            <option :value="2">女</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" :disabled="saving" @click="handleCreate">
            {{ saving ? '保存中...' : '添加' }}
          </button>
          <button class="btn btn-outline" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>

    <div class="card">
      <table v-if="students.length" class="table">
        <thead>
          <tr>
            <th>学号</th>
            <th>姓名</th>
            <th>院系</th>
            <th>班级</th>
            <th>注册状态</th>
            <th>注册时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in students" :key="s.id">
            <td><code>{{ s.student_no }}</code></td>
            <td>{{ s.real_name }}</td>
            <td>{{ s.department || '-' }}</td>
            <td>{{ s.class_name || '-' }}</td>
            <td>
              <span class="status-tag" :class="s.is_registered ? 'yes' : 'no'">
                {{ s.is_registered ? '已注册' : '未注册' }}
              </span>
            </td>
            <td>{{ s.registered_at?.substring(0, 16) || '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无学籍数据，请运行 seed_student_registry.py 导入</div>

      <div v-if="total > pageSize" class="pagination">
        <button class="btn btn-sm btn-outline" :disabled="page <= 1" @click="loadData(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</span>
        <button class="btn btn-sm btn-outline" :disabled="page >= totalPages" @click="loadData(page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStudentRegistry, getDashboard, exportData, createStudentRegistry } from '../../api'

const students = ref([])
const summary = ref({ total: 0, registered: 0, unregistered: 0 })
const keyword = ref('')
const registeredFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const exporting = ref(false)
const showForm = ref(false)
const saving = ref(false)
const form = ref({
  student_no: '',
  real_name: '',
  department: '',
  class_name: '',
  gender: 0,
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadSummary() {
  try {
    const dash = await getDashboard()
    summary.value = {
      total: dash.data.registry_total || 0,
      registered: dash.data.registry_registered || 0,
      unregistered: dash.data.registry_unregistered || 0,
    }
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await loadSummary()
  loadData(1)
})

async function loadData(p) {
  page.value = p
  try {
    const res = await getStudentRegistry({
      page: p,
      page_size: pageSize,
      keyword: keyword.value,
      registered: registeredFilter.value,
    })
    students.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    console.error(e)
    alert(e.message)
  }
}

async function handleExport() {
  exporting.value = true
  try {
    await exportData('student_registry')
  } catch (e) {
    alert(e.message)
  } finally {
    exporting.value = false
  }
}

async function handleCreate() {
  if (!form.value.student_no.trim() || !form.value.real_name.trim()) {
    alert('请填写学号和姓名')
    return
  }
  saving.value = true
  try {
    await createStudentRegistry({
      student_no: form.value.student_no.trim(),
      real_name: form.value.real_name.trim(),
      department: form.value.department.trim(),
      class_name: form.value.class_name.trim(),
      gender: form.value.gender,
    })
    showForm.value = false
    form.value = { student_no: '', real_name: '', department: '', class_name: '', gender: 0 }
    await loadSummary()
    loadData(1)
    alert('学生信息添加成功')
  } catch (e) {
    alert(e.message)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  margin-top: 6px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-card strong {
  display: block;
  font-size: 30px;
  color: var(--primary);
  margin-bottom: 4px;
}

.stat-card.registered strong { color: #52c41a; }
.stat-card.unregistered strong { color: #fa8c16; }

.stat-card span {
  font-size: 15px;
  color: var(--text-muted);
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 16px 20px;
  margin-bottom: 20px;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.status-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.status-tag.yes {
  background: rgba(82, 196, 26, 0.12);
  color: #389e0d;
}

.status-tag.no {
  background: rgba(250, 140, 22, 0.12);
  color: #d46b08;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 0 8px;
  font-size: 15px;
  color: var(--text-secondary);
}

code {
  font-family: monospace;
  font-size: 15px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  width: 440px;
  max-width: 100%;
  padding: 28px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
</style>
