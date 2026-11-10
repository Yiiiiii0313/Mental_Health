<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">消息通知</h1>
      <p class="page-subtitle">
        共 {{ allCount }} 条通知
        <button v-if="unreadCount" class="btn btn-sm btn-outline" style="margin-left:12px" @click="handleReadAll">
          全部标为已读
        </button>
      </p>
    </div>

    <div class="filter-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="filter-tab"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <div class="notification-list">
      <div
        v-for="n in notifications"
        :key="n.id"
        class="card notification-item"
        :class="{ unread: !n.is_read }"
        @click="handleItemClick(n)"
      >
        <div class="notif-icon">{{ typeIcon(n.type) }}</div>
        <div class="notif-body">
          <div class="notif-header">
            <h3>{{ n.title }}</h3>
            <span class="notif-time">{{ n.created_at?.substring(0, 16) }}</span>
          </div>
          <p class="notif-content">{{ n.content }}</p>
          <div class="notif-actions" @click.stop>
            <button v-if="!n.is_read" class="btn btn-sm btn-outline" @click="handleRead(n.id)">标为已读</button>
            <button
              v-if="n.type === 'consultation' && n.related_id"
              class="btn btn-sm btn-primary"
              @click="goConsultation(n.related_id)"
            >查看会话</button>
            <button
              v-if="n.type === 'tree_hole'"
              class="btn btn-sm btn-primary"
              @click="goTreeHole"
            >查看栖心树洞</button>
            <button class="btn btn-sm btn-danger" @click="handleDelete(n.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!notifications.length" class="empty-state card">
      {{ emptyText }}
    </div>
  </div>
</template>

<script setup>
/**
 * 消息通知中心页面
 * 支持全部 / 未读 / 已读筛选
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getNotifications, markNotificationRead,
  markAllNotificationsRead, deleteNotification
} from '../api'

const router = useRouter()
const notifications = ref([])
const total = ref(0)
const unreadCount = ref(0)
const readCount = ref(0)
const allCount = ref(0)
const activeTab = ref('all')

const typeIcons = {
  system: '📢', appointment: '📅', consultation: '💬',
  tree_hole: '🕊️', scale: '📋'
}

const tabs = computed(() => [
  { key: 'all', label: '全部消息', count: allCount.value },
  { key: 'unread', label: '未读', count: unreadCount.value },
  { key: 'read', label: '已读', count: readCount.value },
])

const emptyText = computed(() => {
  if (activeTab.value === 'unread') return '暂无未读通知'
  if (activeTab.value === 'read') return '暂无已读通知'
  return '暂无通知消息'
})

onMounted(() => loadData())

function switchTab(key) {
  activeTab.value = key
  loadData()
}

async function loadData() {
  try {
    const params = { page: 1, page_size: 50 }
    if (activeTab.value === 'unread') params.is_read = 0
    if (activeTab.value === 'read') params.is_read = 1

    const res = await getNotifications(params)
    notifications.value = res.data.list
    total.value = res.data.total
    unreadCount.value = res.data.unread_count
    readCount.value = res.data.read_count
    allCount.value = res.data.all_count
    window.dispatchEvent(new Event('notification-read'))
  } catch (e) { console.error(e) }
}

function typeIcon(type) { return typeIcons[type] || '📢' }

async function handleRead(id) {
  await markNotificationRead(id)
  loadData()
}

async function handleReadAll() {
  await markAllNotificationsRead()
  loadData()
}

async function handleDelete(id) {
  await deleteNotification(id)
  loadData()
}

function goConsultation(id) {
  router.push(`/consultations/${id}`)
}

function goTreeHole() {
  router.push('/tree-hole')
}

async function handleItemClick(n) {
  const wasUnread = !n.is_read
  if (wasUnread) await markNotificationRead(n.id)
  if (n.type === 'consultation' && n.related_id) {
    router.push(`/consultations/${n.related_id}`)
    return
  }
  if (n.type === 'tree_hole' && n.related_id) {
    router.push(`/tree-hole/${n.related_id}`)
    return
  }
  if (wasUnread) loadData()
}
</script>

<style scoped>
.filter-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 1.5px solid var(--border);
  border-radius: 24px;
  background: #fff;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  transition: var(--transition);
}

.filter-tab:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.filter-tab.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.tab-count {
  min-width: 22px;
  padding: 1px 8px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.08);
  font-size: 14px;
  text-align: center;
}

.filter-tab.active .tab-count {
  background: rgba(255, 255, 255, 0.25);
}

.notification-list { display: flex; flex-direction: column; gap: 12px; }

.notification-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  transition: var(--transition);
  cursor: pointer;
}

.notification-item:hover {
  border-color: var(--primary-light);
}

.notification-item.unread {
  border-left: 4px solid var(--primary);
  background: #f8fbfc;
}

.notif-icon { font-size: 30px; flex-shrink: 0; }
.notif-body { flex: 1; }

.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.notif-header h3 { font-size: 17px; font-weight: 600; }
.notif-time { font-size: 14px; color: var(--text-muted); }
.notif-content { font-size: 16px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 10px; }
.notif-actions { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
