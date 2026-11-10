<template>
  <div class="layout">
    <DynamicBackground />
    <!-- 侧边导航栏 -->
    <aside class="sidebar">
      <div class="logo">
        <AppLogo mark size="md" class="logo-mark" />
        <div>
          <span class="logo-text">心屿</span>
          <span class="logo-sub">校园心理健康服务平台</span>
        </div>
      </div>
      <nav class="nav-menu">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
          <span v-if="item.path === '/notifications' && unreadCount > 0" class="nav-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </router-link>
        <router-link v-if="user?.role === 'admin'" to="/admin" class="nav-item">
          <span class="nav-icon">⚙️</span>
          <span>管理后台</span>
        </router-link>
        <router-link v-if="user?.role === 'admin'" to="/admin/agent" class="nav-item">
          <span class="nav-icon">🤖</span>
          <span>多智能体协作</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-badge">
          <div class="user-avatar">
            <img v-if="user?.avatar" :src="user.avatar" alt="头像" class="avatar-img" />
            <span v-else>{{ displayInitial }}</span>
          </div>
          <div class="user-info">
            <span class="user-name">{{ displayName }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
        </div>
        <router-link to="/profile" class="footer-link">个人中心</router-link>
        <button class="footer-link logout" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
/**
 * 主布局组件
 * 包含侧边导航栏和内容区域
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getUnreadCount } from '../api'
import DynamicBackground from '../components/DynamicBackground.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const user = ref(null)
const unreadCount = ref(0)
let pollTimer = null

const navItems = [
  { path: '/home', icon: '🏠', label: '首页' },
  { path: '/scales', icon: '📋', label: '心理测评' },
  { path: '/appointments', icon: '📅', label: '咨询预约' },
  { path: '/articles', icon: '📖', label: '心理文章' },
  { path: '/mood', icon: '💭', label: '心情日记' },
  { path: '/consultations', icon: '💬', label: '在线咨询' },
  { path: '/relaxation', icon: '🎵', label: '放松训练' },
  { path: '/games', icon: '🎮', label: '心理小游戏' },
  { path: '/tree-hole', icon: '🕊️', label: '栖心树洞' },
  { path: '/notifications', icon: '🔔', label: '消息通知' },
]

const roleMap = { student: '学生', counselor: '咨询师', admin: '管理员' }
const roleLabel = computed(() => roleMap[user.value?.role] || '')
const displayName = computed(() => user.value?.nickname || user.value?.real_name || '用户')
const displayInitial = computed(() => displayName.value.charAt(0))

function refreshUser() {
  user.value = JSON.parse(localStorage.getItem('user') || 'null')
}

onMounted(() => {
  refreshUser()
  loadUnread()
  pollTimer = setInterval(loadUnread, 30000)
  window.addEventListener('notification-read', loadUnread)
  window.addEventListener('user-updated', refreshUser)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  window.removeEventListener('notification-read', loadUnread)
  window.removeEventListener('user-updated', refreshUser)
})

async function loadUnread() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data.unread_count
  } catch (e) { /* 静默 */ }
}

/** 退出登录 */
function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  width: 100%;
  position: relative;
  --sidebar-width: 240px;
}

.sidebar {
  width: var(--sidebar-width);
  background: rgba(249, 248, 241, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: var(--text);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  box-shadow: 2px 0 16px rgba(69, 106, 93, 0.06);
  border-right: 1px solid rgba(212, 225, 215, 0.6);
  transition: width 0.25s ease;
}

.logo {
  padding: 28px 22px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(212, 225, 215, 0.6);
}

.logo-mark {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: transparent;
  box-shadow: none;
}

.logo-text {
  display: block;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #456a5d;
}

.logo-sub {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  letter-spacing: 0.3px;
}

.nav-menu {
  flex: 1;
  padding: 20px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  color: var(--text-secondary);
  font-size: 16px;
  border-radius: 10px;
  transition: all 0.2s;
  position: relative;
}

.nav-badge {
  margin-left: auto;
  background: #e85d5d;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.nav-icon {
  width: 22px;
  text-align: center;
  font-size: 18px;
}

.nav-item:hover {
  background: rgba(228, 237, 229, 0.65);
  color: #456a5d;
}

.nav-item.router-link-active {
  background: #e4ede5;
  color: #456a5d;
  font-weight: 600;
  box-shadow: none;
}

.sidebar-footer {
  border-top: 1px solid rgba(212, 225, 215, 0.6);
  padding: 16px;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(228, 237, 229, 0.55);
  border-radius: 10px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #456a5d, #6ba888);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  display: block;
  font-size: 15px;
  font-weight: 600;
}

.user-role {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
}

.footer-link {
  display: block;
  width: 100%;
  padding: 8px 10px;
  color: var(--text-secondary);
  font-size: 15px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.footer-link:hover {
  background: rgba(228, 237, 229, 0.65);
  color: #456a5d;
}

.logout { color: var(--text-muted); }

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: 32px clamp(24px, 3vw, 48px);
  min-height: 100vh;
  min-width: 0;
  width: calc(100% - var(--sidebar-width));
  box-sizing: border-box;
  position: relative;
  z-index: 1;
  transition: margin-left 0.25s ease, width 0.25s ease;
}

/* 宽屏：侧栏略加宽，字号与间距同步放大 */
@media (min-width: 1400px) {
  .layout {
    --sidebar-width: 272px;
  }

  .logo {
    padding: 30px 26px;
    gap: 14px;
  }

  .logo-mark {
    width: 52px;
    height: 52px;
  }

  .logo-text {
    font-size: 20px;
  }

  .logo-sub {
    font-size: 13px;
    margin-top: 3px;
  }

  .nav-menu {
    padding: 22px 14px;
  }

  .nav-item {
    gap: 14px;
    padding: 13px 18px;
    margin-bottom: 5px;
    font-size: 17px;
    border-radius: 12px;
  }

  .nav-icon {
    width: 24px;
    font-size: 20px;
  }

  .nav-badge {
    font-size: 14px;
    padding: 2px 8px;
  }

  .sidebar-footer {
    padding: 18px;
  }

  .user-badge {
    padding: 12px;
    gap: 12px;
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    font-size: 17px;
  }

  .user-name {
    font-size: 16px;
  }

  .user-role {
    font-size: 14px;
  }

  .footer-link {
    padding: 9px 12px;
    font-size: 16px;
    border-radius: 8px;
  }

  .main-content {
    padding: 36px clamp(28px, 3.5vw, 56px);
  }
}

@media (min-width: 1800px) {
  .layout {
    --sidebar-width: 300px;
  }

  .logo {
    padding: 32px 28px;
  }

  .logo-mark {
    width: 56px;
    height: 56px;
  }

  .logo-text {
    font-size: 21px;
  }

  .logo-sub {
    font-size: 14px;
  }

  .nav-menu {
    padding: 24px 16px;
  }

  .nav-item {
    padding: 14px 20px;
    font-size: 18px;
    border-radius: 12px;
  }

  .nav-icon {
    width: 26px;
    font-size: 21px;
  }

  .user-avatar {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }

  .user-name {
    font-size: 17px;
  }

  .footer-link {
    font-size: 17px;
  }

  .main-content {
    padding: 40px clamp(32px, 4vw, 64px);
  }
}
</style>
