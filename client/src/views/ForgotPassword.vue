<template>
  <div class="forgot-page">
    <DynamicBackground contained />
    <div class="forgot-card">
      <AppLogo size="xl" class="page-logo" />
      <h1 class="page-title">找回密码</h1>
      <p class="hint">可通过注册邮箱验证码，或注册时设置的安全问题重置密码</p>

      <div class="tabs">
        <button type="button" :class="{ active: mode === 'email' }" @click="mode = 'email'">邮箱验证码</button>
        <button type="button" :class="{ active: mode === 'question' }" @click="mode = 'question'">安全问题</button>
      </div>

      <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>
      <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>
      <div v-if="devCode" class="alert alert-success">开发模式验证码：{{ devCode }}（未配置邮箱服务时显示）</div>

      <!-- 邮箱途径 -->
      <form v-if="mode === 'email'" @submit.prevent="handleEmailReset">
        <div class="form-group">
          <label>注册邮箱 *</label>
          <input v-model="emailForm.email" type="email" class="form-input" placeholder="请输入注册时填写的邮箱" required />
        </div>
        <div class="form-group code-row">
          <label>验证码 *</label>
          <div class="code-fields">
            <input v-model="emailForm.code" class="form-input" placeholder="6 位验证码" required />
            <button type="button" class="btn btn-outline" :disabled="sending || countdown > 0" @click="handleSendCode">
              {{ countdown > 0 ? `${countdown}s` : (sending ? '发送中...' : '获取验证码') }}
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>新密码 *</label>
          <PasswordInput v-model="emailForm.new_password" placeholder="至少 6 位" required autocomplete="new-password" />
        </div>
        <div class="form-group">
          <label>确认新密码 *</label>
          <PasswordInput v-model="emailForm.confirm" placeholder="再次输入新密码" required autocomplete="new-password" />
        </div>
        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
          {{ loading ? '提交中...' : '重置密码' }}
        </button>
      </form>

      <!-- 安全问题途径 -->
      <form v-else @submit.prevent="handleQuestionReset">
        <div class="form-group">
          <label>用户名 *</label>
          <div class="name-row">
            <input v-model="questionForm.username" class="form-input" placeholder="请输入登录用户名" required />
            <button type="button" class="btn btn-outline" :disabled="loadingQuestion" @click="handleLoadQuestion">
              {{ loadingQuestion ? '查询中...' : '获取问题' }}
            </button>
          </div>
        </div>
        <div v-if="securityQuestion" class="question-box">
          安全问题：{{ securityQuestion }}
        </div>
        <div class="form-group">
          <label>答案 *</label>
          <input v-model="questionForm.security_answer" class="form-input" placeholder="请输入注册时设置的答案" required />
        </div>
        <div class="form-group">
          <label>新密码 *</label>
          <PasswordInput v-model="questionForm.new_password" placeholder="至少 6 位" required autocomplete="new-password" />
        </div>
        <div class="form-group">
          <label>确认新密码 *</label>
          <PasswordInput v-model="questionForm.confirm" placeholder="再次输入新密码" required autocomplete="new-password" />
        </div>
        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
          {{ loading ? '提交中...' : '重置密码' }}
        </button>
      </form>

      <div class="footer-link">
        <router-link to="/login">返回登录</router-link>
        · <router-link to="/register">去注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  sendResetCode,
  resetPasswordByEmail,
  getSecurityQuestion,
  resetPasswordByQuestion,
} from '../api'
import DynamicBackground from '../components/DynamicBackground.vue'
import PasswordInput from '../components/PasswordInput.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const mode = ref('email')
const loading = ref(false)
const sending = ref(false)
const loadingQuestion = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const devCode = ref('')
const securityQuestion = ref('')
const countdown = ref(0)
let timer = null

const emailForm = ref({ email: '', code: '', new_password: '', confirm: '' })
const questionForm = ref({ username: '', security_answer: '', new_password: '', confirm: '' })

function clearAlerts() {
  errorMsg.value = ''
  successMsg.value = ''
}

function startCountdown(sec = 60) {
  countdown.value = sec
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

async function handleSendCode() {
  clearAlerts()
  devCode.value = ''
  if (!emailForm.value.email.trim()) {
    errorMsg.value = '请先填写注册邮箱'
    return
  }
  sending.value = true
  try {
    const res = await sendResetCode({ email: emailForm.value.email.trim() })
    successMsg.value = res.message || '验证码已发送'
    if (res.data?.dev_code) {
      devCode.value = res.data.dev_code
      emailForm.value.code = res.data.dev_code
    }
    startCountdown(60)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    sending.value = false
  }
}

async function handleEmailReset() {
  clearAlerts()
  if (emailForm.value.new_password !== emailForm.value.confirm) {
    errorMsg.value = '两次输入的新密码不一致'
    return
  }
  loading.value = true
  try {
    const res = await resetPasswordByEmail({
      email: emailForm.value.email.trim(),
      code: emailForm.value.code.trim(),
      new_password: emailForm.value.new_password,
    })
    successMsg.value = res.message || '密码已重置'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleLoadQuestion() {
  clearAlerts()
  securityQuestion.value = ''
  if (!questionForm.value.username.trim()) {
    errorMsg.value = '请先填写用户名'
    return
  }
  loadingQuestion.value = true
  try {
    const res = await getSecurityQuestion(questionForm.value.username.trim())
    securityQuestion.value = res.data.security_question
    successMsg.value = '已获取安全问题，请填写答案'
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loadingQuestion.value = false
  }
}

async function handleQuestionReset() {
  clearAlerts()
  if (!securityQuestion.value) {
    errorMsg.value = '请先获取安全问题'
    return
  }
  if (questionForm.value.new_password !== questionForm.value.confirm) {
    errorMsg.value = '两次输入的新密码不一致'
    return
  }
  loading.value = true
  try {
    const res = await resetPasswordByQuestion({
      username: questionForm.value.username.trim(),
      security_answer: questionForm.value.security_answer.trim(),
      new_password: questionForm.value.new_password,
    })
    successMsg.value = res.message || '密码已重置'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  position: relative;
  overflow: hidden;
}

.forgot-card {
  width: 480px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
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

.hint {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.6;
}

.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 18px;
}

.tabs button {
  border: 1px solid var(--border, #dde5ea);
  background: #f7fafb;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  font-size: 15px;
  color: var(--text-secondary, #667);
}

.tabs button.active {
  background: #e8f6ef;
  border-color: #8dcaa8;
  color: #2f6b52;
  font-weight: 600;
}

.code-fields,
.name-row {
  display: flex;
  gap: 10px;
}

.code-fields .form-input,
.name-row .form-input {
  flex: 1;
}

.question-box {
  padding: 12px 14px;
  background: #f3f8f5;
  border-radius: 8px;
  margin-bottom: 14px;
  color: #2f6b52;
  font-size: 15px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
}

.footer-link {
  text-align: center;
  margin-top: 16px;
  font-size: 16px;
  color: var(--text-secondary);
}
</style>
