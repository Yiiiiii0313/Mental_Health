<template>
  <div class="register-page">
    <DynamicBackground contained />
    <div class="register-card">
      <AppLogo size="xl" class="page-logo" />
      <h1 class="page-title">学生注册</h1>
      <p class="register-hint">请使用学籍库中的学号与真实姓名注册；邮箱与安全问题用于找回密码，均为必填</p>

      <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>
      <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>
      <div v-if="verifyMsg" class="alert alert-success">{{ verifyMsg }}</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>学号 *</label>
          <input v-model="form.student_no" class="form-input" placeholder="请输入学号" required />
        </div>

        <div class="form-group">
          <label>真实姓名 *</label>
          <div class="name-row">
            <input v-model="form.real_name" class="form-input" placeholder="须与学籍库姓名一致" required />
            <button type="button" class="btn btn-outline verify-btn" :disabled="verifying" @click="handleVerify">
              {{ verifying ? '校验中...' : '校验学籍' }}
            </button>
          </div>
        </div>

        <div v-if="verifiedInfo" class="verified-box">
          <span>✅ 学籍校验通过</span>
          <span v-if="verifiedInfo.department">{{ verifiedInfo.department }} · {{ verifiedInfo.class_name }}</span>
        </div>

        <div class="form-group">
          <label>用户名 *</label>
          <input v-model="form.username" class="form-input" placeholder="登录用户名" required />
        </div>

        <div class="form-group">
          <label>密码 *</label>
          <PasswordInput v-model="form.password" placeholder="至少 6 位" required autocomplete="new-password" />
        </div>

        <div class="form-group">
          <label>邮箱 *</label>
          <input v-model="form.email" type="email" class="form-input" placeholder="用于接收找回密码验证码" required />
        </div>

        <div class="form-group">
          <label>安全问题 *</label>
          <select v-model="questionPreset" class="form-select" @change="onQuestionPresetChange">
            <option v-for="q in questionOptions" :key="q" :value="q">{{ q }}</option>
            <option value="__custom__">自定义问题…</option>
          </select>
          <input
            v-if="questionPreset === '__custom__'"
            v-model="form.security_question"
            class="form-input custom-q"
            placeholder="请输入自定义安全问题，如：你的名字是什么？"
            required
          />
        </div>

        <div class="form-group">
          <label>安全问题答案 *</label>
          <input v-model="form.security_answer" class="form-input" placeholder="请牢记答案，用于找回密码" required />
        </div>

        <div class="form-group">
          <label>手机号</label>
          <input v-model="form.phone" class="form-input" placeholder="选填" />
        </div>

        <div class="form-group">
          <label>性别</label>
          <select v-model="form.gender" class="form-select">
            <option :value="0">未知</option>
            <option :value="1">男</option>
            <option :value="2">女</option>
          </select>
        </div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>
      </form>

      <div class="login-link">
        已有账号？<router-link to="/login">返回登录</router-link>
        · <router-link to="/forgot-password">忘记密码</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, verifyStudent, getSecurityQuestions } from '../api'
import DynamicBackground from '../components/DynamicBackground.vue'
import PasswordInput from '../components/PasswordInput.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const loading = ref(false)
const verifying = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const verifyMsg = ref('')
const verifiedInfo = ref(null)
const questionOptions = ref([
  '你的名字是什么？',
  '你的生日是什么？',
  '你小学的名称是什么？',
  '你最喜欢的老师叫什么？',
])
const questionPreset = ref('你的名字是什么？')
const form = ref({
  username: '',
  password: '',
  student_no: '',
  real_name: '',
  phone: '',
  email: '',
  gender: 0,
  security_question: '你的名字是什么？',
  security_answer: '',
})

function onQuestionPresetChange() {
  if (questionPreset.value === '__custom__') {
    form.value.security_question = ''
  } else {
    form.value.security_question = questionPreset.value
  }
}

onMounted(async () => {
  try {
    const res = await getSecurityQuestions()
    if (res.data?.questions?.length) {
      questionOptions.value = res.data.questions
      questionPreset.value = res.data.questions[0]
      form.value.security_question = res.data.questions[0]
    }
  } catch {
    /* 使用本地默认问题列表 */
  }
})

async function handleVerify() {
  if (!form.value.student_no.trim() || !form.value.real_name.trim()) {
    errorMsg.value = '请先填写学号和姓名'
    return
  }
  verifying.value = true
  errorMsg.value = ''
  verifyMsg.value = ''
  verifiedInfo.value = null
  try {
    const res = await verifyStudent({
      student_no: form.value.student_no.trim(),
      real_name: form.value.real_name.trim(),
    })
    verifiedInfo.value = res.data
    verifyMsg.value = '学籍信息校验通过，可以注册'
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    verifying.value = false
  }
}

async function handleRegister() {
  if (!form.value.email.trim()) {
    errorMsg.value = '请填写注册邮箱'
    return
  }
  if (!form.value.security_question.trim() || !form.value.security_answer.trim()) {
    errorMsg.value = '请填写安全问题与答案'
    return
  }
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await register({
      ...form.value,
      student_no: form.value.student_no.trim(),
      real_name: form.value.real_name.trim(),
      email: form.value.email.trim(),
      security_question: form.value.security_question.trim(),
      security_answer: form.value.security_answer.trim(),
    })
    successMsg.value = '注册成功，即将跳转登录页...'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  position: relative;
  overflow: hidden;
}

.register-card {
  width: 480px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  padding: 36px;
  position: relative;
  z-index: 1;
}

.page-logo {
  display: block;
  margin: 0 auto 12px;
}

.page-title {
  text-align: center;
}

.register-hint {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.6;
}

.name-row {
  display: flex;
  gap: 10px;
}

.name-row .form-input {
  flex: 1;
}

.verify-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

.verified-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  background: #f0faf4;
  border-radius: 8px;
  font-size: 15px;
  color: #389e0d;
  margin-bottom: 12px;
}

.custom-q {
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  font-size: 16px;
  color: var(--text-secondary);
}
</style>
