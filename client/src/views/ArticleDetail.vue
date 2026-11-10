<template>
  <div class="detail-page">
    <router-link to="/articles" class="back-link">← 返回心理文章</router-link>

    <div v-if="loading" class="empty-state card">加载中...</div>

    <template v-else-if="article">
      <section class="reader-section" :style="{ '--cat-color': categoryStyle.color }">
        <div class="reader-cover">
          <span class="cover-icon">{{ categoryStyle.icon }}</span>
          <div class="cover-waves">
            <span v-for="i in 5" :key="i" class="wave"></span>
          </div>
          <div class="cover-meta">
            <span class="meta-tag">{{ article.category }}</span>
            <span class="meta-tag">📝 约 {{ wordCount }} 字</span>
            <span class="meta-tag">👁 {{ article.view_count }} 次阅读</span>
          </div>
        </div>
      </section>

      <section class="info-section card">
        <div class="info-header">
          <div class="info-tags">
            <span class="tag tag-category">{{ article.category }}</span>
            <span class="type-tag">✍️ {{ article.author_name }}</span>
            <span class="duration-tag">📅 {{ formatDate(article.created_at) }}</span>
          </div>
          <h1>{{ article.title }}</h1>
          <div class="action-bar">
            <button class="action-btn" :class="{ active: article.is_liked }" @click="handleLike">
              {{ article.is_liked ? '❤️' : '🤍' }} {{ article.like_count || 0 }} 点赞
            </button>
            <button class="action-btn" :class="{ active: article.is_favorited }" @click="handleFavorite">
              {{ article.is_favorited ? '⭐' : '☆' }} {{ article.is_favorited ? '已收藏' : '收藏' }}
            </button>
          </div>
        </div>

        <div class="article-content">
          <p v-for="(para, i) in paragraphs" :key="i">{{ para }}</p>
        </div>

        <div class="tips-box">
          <h3>阅读建议</h3>
          <ul>
            <li>选择安静的环境，专注阅读每一段落</li>
            <li>遇到有共鸣的内容，可以记录到心情日记中</li>
            <li>若内容引发强烈不适，请及时寻求专业心理咨询</li>
          </ul>
        </div>
      </section>

      <section v-if="related.length" class="related-section">
        <h2 class="section-title">同分类推荐</h2>
        <div class="related-grid">
          <router-link
            v-for="r in related"
            :key="r.id"
            :to="`/articles/${r.id}`"
            class="related-card card"
          >
            <span class="related-icon">{{ getCategoryStyle(r.category).icon }}</span>
            <div>
              <h4>{{ r.title }}</h4>
              <span class="related-meta">{{ r.category }} · 👁 {{ r.view_count || 0 }}</span>
            </div>
          </router-link>
        </div>
      </section>
    </template>

    <div v-else class="empty-state card">文章不存在或已下架</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  getArticle, getArticles,
  likeArticle, unlikeArticle, favoriteArticle, unfavoriteArticle
} from '../api'

const route = useRoute()
const article = ref(null)
const related = ref([])
const loading = ref(true)

const CATEGORY_META = {
  '学业压力': { icon: '📚', color: '#456a5d' },
  '人际关系': { icon: '🤝', color: '#5a8575' },
  '心理疾病': { icon: '💚', color: '#6ba888' },
  '自我调节': { icon: '🧘', color: '#d48ab4' },
}

const paragraphs = computed(() => {
  if (!article.value?.content) return []
  return article.value.content.split('\n').filter(p => p.trim())
})

const wordCount = computed(() => article.value?.content?.length || 0)

const categoryStyle = computed(() =>
  getCategoryStyle(article.value?.category)
)

onMounted(() => loadDetail())

watch(() => route.params.id, () => loadDetail())

async function loadDetail() {
  loading.value = true
  try {
    const [detailRes, listRes] = await Promise.all([
      getArticle(route.params.id),
      getArticles({ page: 1, page_size: 100 })
    ])
    article.value = detailRes.data
    related.value = (listRes.data?.list || [])
      .filter(a => a.id !== article.value.id && a.category === article.value.category)
      .slice(0, 3)
  } catch (e) {
    article.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getCategoryStyle(category) {
  return CATEGORY_META[category] || { icon: '📖', color: '#456a5d' }
}

function formatDate(value) {
  if (!value) return ''
  return String(value).substring(0, 10)
}

async function handleLike() {
  if (!article.value) return
  try {
    if (article.value.is_liked) {
      const res = await unlikeArticle(article.value.id)
      article.value.is_liked = false
      article.value.like_count = res.data.like_count
    } else {
      const res = await likeArticle(article.value.id)
      article.value.is_liked = true
      article.value.like_count = res.data.like_count
    }
  } catch (e) { alert(e.message) }
}

async function handleFavorite() {
  if (!article.value) return
  try {
    if (article.value.is_favorited) {
      await unfavoriteArticle(article.value.id)
      article.value.is_favorited = false
    } else {
      await favoriteArticle(article.value.id)
      article.value.is_favorited = true
    }
  } catch (e) { alert(e.message) }
}
</script>

<style scoped>
.detail-page {
  max-width: 960px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 20px;
  font-size: 16px;
  color: var(--primary);
  font-weight: 500;
}

.reader-section {
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: var(--shadow-lg);
  background: linear-gradient(160deg, color-mix(in srgb, var(--cat-color) 55%, #2d4a42), color-mix(in srgb, var(--cat-color) 35%, #3d6a5d));
  padding: 48px 32px;
}

.reader-cover {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.cover-icon {
  font-size: 84px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.2));
}

.cover-waves {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 32px;
}

.wave {
  width: 6px;
  height: 12px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.35);
  animation: wave 1.2s ease-in-out infinite;
}

.wave:nth-child(1) { animation-delay: 0s; }
.wave:nth-child(2) { animation-delay: 0.2s; }
.wave:nth-child(3) { animation-delay: 0.4s; }
.wave:nth-child(4) { animation-delay: 0.2s; }
.wave:nth-child(5) { animation-delay: 0s; }

@keyframes wave {
  0%, 100% { height: 12px; }
  50% { height: 28px; }
}

.cover-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.meta-tag {
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
  backdrop-filter: blur(4px);
}

.info-section {
  padding: 32px;
  margin-bottom: 28px;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.type-tag,
.duration-tag {
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 14px;
  background: #f0f4f8;
  color: var(--text-secondary);
}

.info-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--text);
  line-height: 1.4;
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 18px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 16px;
  transition: var(--transition);
}

.action-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.action-btn.active {
  border-color: var(--primary);
  background: rgba(69, 106, 93, 0.08);
  color: var(--primary);
}

.article-content p {
  font-size: 18px;
  line-height: 2;
  color: #334155;
  margin-bottom: 1.2em;
  text-indent: 2em;
  text-align: justify;
}

.tips-box {
  margin-top: 28px;
  padding: 20px 24px;
  background: #f8fbfd;
  border-radius: var(--radius);
  border-left: 4px solid var(--primary);
}

.tips-box h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text);
}

.tips-box ul {
  padding-left: 18px;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.9;
}

.related-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 14px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.related-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  color: inherit;
  transition: var(--transition);
}

.related-card:hover {
  border-color: var(--primary);
  transform: translateX(4px);
}

.related-icon {
  font-size: 34px;
  flex-shrink: 0;
}

.related-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.related-meta {
  font-size: 14px;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .reader-section { padding: 32px 20px; }
  .info-section { padding: 24px 20px; }
  .info-header h1 { font-size: 24px; }
}
</style>
