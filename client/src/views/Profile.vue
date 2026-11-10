<template>
  <div>
    <h1 class="page-title">个人中心</h1>

    <div class="profile-layout">
      <!-- 个人信息 -->
      <div class="card">
        <h2 class="section-title">基本信息</h2>
        <div v-if="msg" class="alert" :class="msgType">{{ msg }}</div>

        <div class="avatar-section">
          <div class="avatar-preview">
            <img v-if="form.avatar" :src="form.avatar" alt="头像" class="avatar-img" />
            <div v-else class="avatar-placeholder">{{ displayInitial }}</div>
          </div>
          <div class="avatar-actions">
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              class="file-input"
              @change="handleAvatarSelect"
            />
            <button type="button" class="btn btn-outline" :disabled="uploadingAvatar" @click="triggerAvatarInput">
              {{ uploadingAvatar ? '上传中...' : '更换头像' }}
            </button>
            <p class="avatar-hint">支持 jpg/png/gif/webp，≤5MB</p>
          </div>
        </div>

        <form @submit.prevent="handleUpdate">
          <div class="form-group">
            <label>用户名</label>
            <input :value="profile?.username" class="form-input" disabled />
          </div>
          <div class="form-group">
            <label>昵称</label>
            <input v-model="form.nickname" class="form-input" placeholder="用于平台展示的昵称" maxlength="20" />
          </div>
          <div class="form-group">
            <label>真实姓名</label>
            <input v-model="form.real_name" class="form-input" placeholder="用于预约咨询等正式场景" />
          </div>
          <div class="form-group">
            <label>手机号</label>
            <input v-model="form.phone" class="form-input" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="form.email" class="form-input" />
          </div>
          <div class="form-group">
            <label>性别</label>
            <select v-model="form.gender" class="form-select">
              <option :value="0">未知</option>
              <option :value="1">男</option>
              <option :value="2">女</option>
            </select>
          </div>
          <div class="form-group">
            <label>角色</label>
            <input :value="roleMap[profile?.role]" class="form-input" disabled />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="saving">保存修改</button>
        </form>
      </div>

      <!-- 修改密码 -->
      <div class="card">
        <h2 class="section-title">修改密码</h2>
        <div v-if="pwdMsg" class="alert" :class="pwdMsgType">{{ pwdMsg }}</div>
        <form @submit.prevent="handleChangePwd">
          <div class="form-group">
            <label>原密码</label>
            <PasswordInput v-model="pwdForm.old_password" required autocomplete="current-password" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <PasswordInput v-model="pwdForm.new_password" required autocomplete="new-password" />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="changingPwd">修改密码</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 个人中心页面
 * 支持自定义头像、昵称及基本信息管理
 */
import { ref, computed, onMounted } from 'vue'
import { getProfile, updateProfile, uploadAvatar, changePassword } from '../api'
import PasswordInput from '../components/PasswordInput.vue'

const profile = ref(null)
const form = ref({ real_name: '', nickname: '', phone: '', email: '', gender: 0, avatar: '' })
const pwdForm = ref({ old_password: '', new_password: '' })
const saving = ref(false)
const uploadingAvatar = ref(false)
const msg = ref('')
const msgType = ref('')
const pwdMsg = ref('')
const pwdMsgType = ref('')
const avatarInputRef = ref(null)

const roleMap = { student: '学生', counselor: '咨询师', admin: '管理员' }

const displayInitial = computed(() => {
  const name = form.value.nickname || form.value.real_name || 'U'
  return name.charAt(0)
})

onMounted(async () => {
  try {
    const res = await getProfile()
    profile.value = res.data
    form.value = {
      real_name: res.data.real_name,
      nickname: res.data.nickname || '',
      phone: res.data.phone || '',
      email: res.data.email || '',
      gender: res.data.gender || 0,
      avatar: res.data.avatar || ''
    }
  } catch (e) { console.error(e) }
})

function triggerAvatarInput() {
  avatarInputRef.value?.click()
}

function syncLocalUser(data) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  Object.assign(user, {
    real_name: data.real_name,
    nickname: data.nickname,
    avatar: data.avatar,
    phone: data.phone,
    email: data.email,
    gender: data.gender
  })
  localStorage.setItem('user', JSON.stringify(user))
  window.dispatchEvent(new Event('user-updated'))
}

async function handleAvatarSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploadingAvatar.value = true
  msg.value = ''
  try {
    const res = await uploadAvatar(file)
    form.value.avatar = res.data.avatar
    profile.value = { ...profile.value, avatar: res.data.avatar }
    syncLocalUser({ ...form.value, ...profile.value })
    msg.value = '头像更新成功'
    msgType.value = 'alert-success'
  } catch (e) {
    msg.value = e.message
    msgType.value = 'alert-error'
  } finally {
    uploadingAvatar.value = false
    if (avatarInputRef.value) avatarInputRef.value.value = ''
  }
}

/** 更新个人信息 */
async function handleUpdate() {
  saving.value = true
  msg.value = ''
  try {
    const res = await updateProfile(form.value)
    profile.value = res.data
    form.value.nickname = res.data.nickname || ''
    form.value.avatar = res.data.avatar || ''
    syncLocalUser(res.data)
    msg.value = '信息更新成功'
    msgType.value = 'alert-success'
  } catch (e) {
    msg.value = e.message
    msgType.value = 'alert-error'
  } finally {
    saving.value = false
  }
}

/** 修改密码 */
async function handleChangePwd() {
  changingPwd.value = true
  pwdMsg.value = ''
  try {
    await changePassword(pwdForm.value)
    pwdMsg.value = '密码修改成功'
    pwdMsgType.value = 'alert-success'
    pwdForm.value = { old_password: '', new_password: '' }
  } catch (e) {
    pwdMsg.value = e.message
    pwdMsgType.value = 'alert-error'
  } finally {
    changingPwd.value = false
  }
}
</script>

<style scoped>
.profile-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #4a90a4, #7ec8a0);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 30px;
  font-weight: 600;
}

.avatar-actions { display: flex; flex-direction: column; gap: 6px; }
.file-input { display: none; }
.btn-outline {
  background: #fff;
  border: 1px solid #4a90a4;
  color: #4a90a4;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  width: fit-content;
}
.avatar-hint { font-size: 14px; color: var(--text-muted); margin: 0; }

@media (max-width: 900px) {
  .profile-layout { grid-template-columns: 1fr; }
}
</style>
