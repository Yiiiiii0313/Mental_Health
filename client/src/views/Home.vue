<template>
  <div class="home">
    <div class="welcome-banner">
      <div class="banner-content">
        <p class="banner-greeting">你好，{{ user?.real_name }} 👋</p>
        <h1>关爱心灵，从了解自己开始</h1>
        <p class="banner-desc">心屿校园心理健康服务平台为你提供专业测评、咨询预约、心情记录等一站式服务。</p>
      </div>
      <div class="banner-decoration">
        <div class="deco-circle c1"></div>
        <div class="deco-circle c2"></div>
        <div class="deco-circle c3"></div>
      </div>
    </div>

    <RiskInsightCard />

    <div class="quick-actions">
      <router-link v-for="item in actions" :key="item.path" :to="item.path" class="action-card" :style="{ '--accent': item.color }">
        <div class="action-icon-wrap">{{ item.icon }}</div>
        <span class="action-title">{{ item.title }}</span>
        <span class="action-desc">{{ item.desc }}</span>
      </router-link>
    </div>

    <div class="home-grid">
      <div class="card panel-card">
        <h2 class="section-title"><span>📢</span> 最新公告</h2>
        <div v-if="announcements.length" class="announcement-list">
          <router-link
            v-for="item in announcements"
            :key="item.id"
            :to="`/announcements/${item.id}`"
            class="announcement-item"
          >
            <span class="ann-dot"></span>
            <span class="ann-title">{{ item.title }}</span>
            <span class="ann-date">{{ formatDate(item.created_at) }}</span>
            <span class="ann-arrow">→</span>
          </router-link>
        </div>
        <div v-else class="empty-state">暂无公告</div>
      </div>

      <div class="card panel-card">
        <h2 class="section-title"><span>📖</span> 推荐文章</h2>
        <div v-if="articles.length" class="article-list">
          <router-link v-for="item in articles" :key="item.id" :to="`/articles/${item.id}`" class="article-item">
            <div class="article-item-main">
              <span class="article-title">{{ item.title }}</span>
              <span class="article-meta">
                <span class="tag tag-category">{{ item.category }}</span>
                {{ item.view_count }} 次阅读
              </span>
            </div>
            <span class="article-arrow">→</span>
          </router-link>
        </div>
        <div v-else class="empty-state">暂无文章</div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 首页组件
 */
import { ref, onMounted } from 'vue'
import { getAnnouncements, getArticles } from '../api'
import RiskInsightCard from '../components/RiskInsightCard.vue'

const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const announcements = ref([])
const articles = ref([])

const actions = [
  { path: '/scales', icon: '📋', title: '心理测评', desc: '专业量表自评', color: '#456a5d' },
  { path: '/appointments', icon: '📅', title: '咨询预约', desc: '预约心理咨询师', color: '#6ba888' },
  { path: '/mood', icon: '💭', title: '心情日记', desc: '记录每日心情', color: '#5a8575' },
  { path: '/consultations', icon: '💬', title: '在线咨询', desc: '与咨询师交流', color: '#7b9aaa' },
  { path: '/games', icon: '🎮', title: '心理小游戏', desc: '趣味互动调节情绪', color: '#e8a54b' },
]

onMounted(async () => {
  try {
    const [annRes, artRes] = await Promise.all([
      getAnnouncements({ page: 1, page_size: 5 }),
      getArticles({ page: 1, page_size: 4 })
    ])
    announcements.value = annRes.data.list
    articles.value = artRes.data.list
  } catch (e) { console.error(e) }
})

function formatDate(dateStr) {
  return dateStr ? dateStr.substring(0, 10) : ''
}
</script>

<style scoped>
.home {
  position: relative;
  width: 100%;
}

.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, #fee8c8 0%, #f0f5f0 55%, #d4f1e0 100%);
  color: #456a5d;
  padding: 40px 36px;
  border-radius: var(--radius-lg);
  margin-bottom: 28px;
  overflow: hidden;
  border: 1px solid rgba(200, 220, 200, 0.45);
}

.banner-greeting {
  font-size: 17px;
  color: #5a8575;
  margin-bottom: 8px;
}

.welcome-banner h1 {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
}

.banner-desc {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 480px;
  line-height: 1.7;
}

.banner-decoration {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 200px;
  pointer-events: none;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(212, 241, 224, 0.35);
}
.c1 { width: 120px; height: 120px; right: 30px; top: -20px; }
.c2 { width: 80px; height: 80px; right: 100px; bottom: 20px; }
.c3 { width: 50px; height: 50px; right: 20px; bottom: 50px; background: rgba(255,255,255,0.12); }

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.action-card {
  background: #fff;
  border-radius: var(--radius);
  padding: 24px 20px;
  text-align: center;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  color: inherit;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent);
}

.action-icon-wrap {
  width: 52px;
  height: 52px;
  margin: 0 auto 12px;
  background: color-mix(in srgb, var(--accent) 12%, white);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.action-title {
  display: block;
  font-weight: 600;
  font-size: 17px;
  margin-bottom: 4px;
  color: var(--text);
}

.action-desc {
  display: block;
  font-size: 14px;
  color: var(--text-muted);
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel-card { padding: 28px; }

.announcement-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-light);
  font-size: 16px;
  color: inherit;
  transition: var(--transition);
}

.announcement-item:hover {
  padding-left: 6px;
}

.announcement-item:hover .ann-title {
  color: var(--primary);
}

.announcement-item:hover .ann-arrow {
  opacity: 1;
  transform: translateX(4px);
}

.ann-arrow {
  color: var(--primary);
  opacity: 0;
  transition: var(--transition);
  font-size: 15px;
}

.ann-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  flex-shrink: 0;
}

.ann-title { flex: 1; color: var(--text); }
.ann-date { color: var(--text-muted); font-size: 14px; }

.article-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
  color: inherit;
  transition: var(--transition);
}

.article-item:hover {
  padding-left: 6px;
}

.article-item:hover .article-title { color: var(--primary); }
.article-item:hover .article-arrow { opacity: 1; transform: translateX(4px); }

.article-title {
  display: block;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 6px;
  transition: var(--transition);
}

.article-meta {
  font-size: 14px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}

.article-arrow {
  color: var(--primary);
  opacity: 0;
  transition: var(--transition);
  font-size: 18px;
}

@media (max-width: 900px) {
  .quick-actions { grid-template-columns: repeat(2, 1fr); }
  .home-grid { grid-template-columns: 1fr; }
}
</style>
