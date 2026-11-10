<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h1 class="page-title" style="margin:0">用户管理</h1>
      <router-link to="/admin" class="btn btn-outline">返回后台</router-link>
    </div>

    <!-- 角色筛选 -->
    <div class="filter-bar">
      <button
        v-for="r in roleFilters"
        :key="r.value"
        class="category-btn"
        :class="{ active: currentRole === r.value }"
        @click="filterRole(r.value)"
      >{{ r.label }}</button>
      <button class="btn btn-primary" style="margin-left:auto" @click="showForm = true">添加用户</button>
    </div>

    <!-- 用户列表 -->
    <div class="card">
      <table v-if="users.length" class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>姓名</th>
            <th>角色</th>
            <th>手机</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.real_name }}</td>
            <td>{{ roleMap[u.role] }}</td>
            <td>{{ u.phone || '-' }}</td>
            <td>{{ u.status === 1 ? '正常' : '禁用' }}</td>
            <td>{{ u.created_at?.substring(0, 10) }}</td>
            <td>
              <button
                v-if="u.status === 1"
                class="btn btn-sm btn-danger"
                @click="toggleStatus(u.id, 0)"
              >禁用</button>
              <button
                v-else
                class="btn btn-sm btn-primary"
                @click="toggleStatus(u.id, 1)"
              >启用</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无用户</div>
    </div>

    <!-- 添加用户弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="card modal-content">
        <h2 class="section-title">添加用户</h2>
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" class="form-input" />
        </div>
        <div class="form-group">
          <label>密码（默认123456）</label>
          <PasswordInput v-model="form.password" autocomplete="new-password" />
        </div>
        <div class="form-group">
          <label>姓名</label>
          <input v-model="form.real_name" class="form-input" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role" class="form-select">
            <option value="student">学生</option>
            <option value="counselor">咨询师</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <div style="display:flex;gap:12px;margin-top:16px">
          <button class="btn btn-primary" @click="handleCreate">创建</button>
          <button class="btn btn-outline" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 用户管理页面（管理员）
 */
import { ref, onMounted } from 'vue'
import { getUsers, createUser, toggleUserStatus } from '../../api'
import PasswordInput from '../../components/PasswordInput.vue'

const users = ref([])
const currentRole = ref('')
const showForm = ref(false)
const form = ref({ username: '', password: '123456', real_name: '', role: 'student' })

const roleMap = { student: '学生', counselor: '咨询师', admin: '管理员' }
const roleFilters = [
  { label: '全部', value: '' },
  { label: '学生', value: 'student' },
  { label: '咨询师', value: 'counselor' },
  { label: '管理员', value: 'admin' }
]

onMounted(() => loadUsers())

async function loadUsers() {
  try {
    const res = await getUsers({ role: currentRole.value, page: 1, page_size: 50 })
    users.value = res.data.list
  } catch (e) { console.error(e) }
}

function filterRole(role) {
  currentRole.value = role
  loadUsers()
}

async function handleCreate() {
  try {
    await createUser(form.value)
    alert('用户创建成功')
    showForm.value = false
    form.value = { username: '', password: '123456', real_name: '', role: 'student' }
    loadUsers()
  } catch (e) { alert(e.message) }
}

async function toggleStatus(id, status) {
  try {
    await toggleUserStatus(id, { status })
    loadUsers()
  } catch (e) { alert(e.message) }
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}
.category-btn {
  padding: 6px 16px;
  border: 1px solid #e8ecef;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 15px;
}
.category-btn.active { background: #4a90a4; color: #fff; border-color: #4a90a4; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal-content { width: 400px; }
.section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
</style>
