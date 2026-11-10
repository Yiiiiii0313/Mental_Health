<template>
  <div class="login-page">
    <DynamicBackground contained />
    <div class="login-left">
      <div class="deco-circle c1"></div>
      <div class="deco-circle c2"></div>
      <div class="deco-circle c3"></div>

      <div class="login-left-inner">
        <div class="brand">
          <AppLogo size="xl" class="brand-logo" />
          <h1>心屿校园心理健康服务平台</h1>
          <p>关爱心灵，健康成长</p>
        </div>
        <ul class="features">
          <li><span class="feature-icon">📋</span>专业心理量表测评</li>
          <li><span class="feature-icon">📅</span>在线咨询预约</li>
          <li><span class="feature-icon">💭</span>心情日记记录</li>
          <li><span class="feature-icon">💬</span>师生在线交流</li>
        </ul>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="card-header">
          <div class="card-logo-wrap">
            <AppLogo size="xl" />
          </div>
          <h2>欢迎登录</h2>
          <p class="login-hint">请输入账号和密码</p>
        </div>

        <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="form.username" class="form-input" placeholder="请输入用户名" required />
          </div>
          <div class="form-group">
            <label>密码</label>
            <PasswordInput v-model="form.password" placeholder="请输入密码" required autocomplete="current-password" />
          </div>
          <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>

        <div class="login-footer">
          <router-link to="/forgot-password">忘记密码？</router-link>
          <span class="footer-sep">·</span>
          还没有账号？<router-link to="/register">立即注册</router-link>
        </div>

        <div class="demo-accounts">
          <p>测试账号（密码 123456）</p>
          <div class="demo-list">
            <span @click="fillAccount('admin')">管理员</span>
            <span @click="fillAccount('counselor1')">咨询师</span>
            <span @click="fillAccount('student1')">学生</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 登录页面组件
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api'
import PasswordInput from '../components/PasswordInput.vue'
import DynamicBackground from '../components/DynamicBackground.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const loading = ref(false)
const errorMsg = ref('')
const form = ref({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await login(form.value)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    router.push('/home')
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}

function fillAccount(username) {
  form.value.username = username
  form.value.password = '123456'
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  position: relative;
  overflow: hidden;
}

.login-left {
  position: relative;
  z-index: 1;
  background: linear-gradient(145deg, #fee8c8 0%, #f0f5f0 50%, #d4f1e0 100%);
  color: #456a5d;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(32px, 5vw, 64px);
  overflow: hidden;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(212, 241, 224, 0.35);
  pointer-events: none;
}

.c1 { width: 320px; height: 320px; top: -80px; right: -60px; animation: loginDrift1 22s ease-in-out infinite; }
.c2 { width: 200px; height: 200px; bottom: 10%; left: -40px; background: rgba(254, 232, 200, 0.35); animation: loginDrift2 26s ease-in-out infinite; }
.c3 { width: 120px; height: 120px; bottom: 25%; right: 15%; background: rgba(180, 210, 190, 0.3); animation: loginDrift3 20s ease-in-out infinite; }

@keyframes loginDrift1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-25px, 20px); }
}
@keyframes loginDrift2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -15px); }
}
@keyframes loginDrift3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-15px, -20px); }
}

.login-left-inner {
  position: relative;
  z-index: 1;
  max-width: 480px;
  width: 100%;
}

.brand-logo {
  display: block;
  margin: 0 auto 20px;
  filter: drop-shadow(0 8px 20px rgba(107, 201, 160, 0.22));
}

.brand {
  text-align: center;
}

.brand h1 {
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 700;
  margin-bottom: 12px;
  line-height: 1.3;
  letter-spacing: 0.5px;
}

.brand p {
  font-size: 19px;
  color: #5a8575;
}

.features {
  list-style: none;
  margin-top: 40px;
  display: grid;
  gap: 14px;
}

.features li {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  font-size: 17px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(4px);
}

.feature-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.login-right {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(24px, 4vw, 48px);
  background: rgba(248, 251, 253, 0.72);
  backdrop-filter: blur(6px);
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.login-right::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(107, 201, 160, 0.12) 0%, transparent 70%);
  top: -100px;
  right: -80px;
  animation: loginDrift2 30s ease-in-out infinite;
  pointer-events: none;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  padding: 40px 36px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
}

.card-header {
  text-align: center;
  margin-bottom: 28px;
}

.card-logo-wrap {
  width: 220px;
  height: 220px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card h2 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.login-hint {
  font-size: 16px;
  color: var(--text-muted);
}

.login-btn {
  width: 100%;
  padding: 13px;
  font-size: 17px;
  margin-top: 8px;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 16px;
  color: var(--text-muted);
}

.footer-sep {
  margin: 0 8px;
  color: var(--border, #ccd);
}

.demo-accounts {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  text-align: center;
}

.demo-accounts p {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.demo-list {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.demo-list span {
  padding: 8px 16px;
  background: #f0f4f8;
  border-radius: 20px;
  cursor: pointer;
  font-size: 15px;
  color: var(--primary);
  transition: var(--transition);
}

.demo-list span:hover {
  background: #dce8ee;
  transform: translateY(-1px);
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-left {
    min-height: 280px;
    padding: 40px 32px;
  }

  .login-left-inner {
    max-width: 100%;
  }

  .features {
    grid-template-columns: 1fr 1fr;
    margin-top: 28px;
  }
}

@media (max-width: 600px) {
  .login-left { display: none; }

  .login-right {
    min-height: 100vh;
    padding: 24px 20px;
  }

  .login-card {
    max-width: 100%;
    padding: 32px 24px;
    box-shadow: var(--shadow);
  }

  .features { grid-template-columns: 1fr; }
}
</style>
