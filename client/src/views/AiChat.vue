<template>
  <div class="ai-chat-page">
    <aside class="session-panel card">
      <div class="panel-header">
        <router-link to="/consultations" class="back-link">← 返回</router-link>
        <h2>AI心理助手</h2>
        <button class="btn btn-sm btn-primary" @click="handleNewSession">新对话</button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="switchSession(s.id)"
        >
          <span class="session-icon">🤖</span>
          <div class="session-info">
            <span class="session-title">{{ s.title }}</span>
            <span class="session-time">{{ s.updated_at?.substring(0, 16) }}</span>
          </div>
          <button
            class="session-delete-btn"
            title="删除对话"
            @click.stop="handleDelete(s.id)"
          >✕</button>
        </div>
        <div v-if="!sessions.length" class="empty-hint">点击「新对话」开始聊天</div>
      </div>
    </aside>

    <main class="chat-main">
      <div class="chat-header card">
        <div class="ai-avatar">🌿</div>
        <div>
          <h3>小暖 · AI心理助手</h3>
          <p>24小时在线倾听，为你提供情绪疏导与心理支持</p>
        </div>
        <span class="ai-badge">AI</span>
        <span v-if="ragActive" class="rag-badge" title="已启用心理健康知识库增强">知识增强</span>
        <span v-else class="rag-badge rag-badge-off" title="知识库未就绪：请确认 RAG_ENABLED=1 且已执行 seed_knowledge_base.py">知识库未开</span>
      </div>

      <div ref="messageBox" class="chat-messages">
        <template v-for="msg in messages" :key="msg.id">
          <div
            class="message-item"
            :class="{ mine: msg.role === 'user', assistant: msg.role === 'assistant' }"
          >
            <div class="message-sender">
              {{ msg.role === 'user' ? '我' : '小暖' }}
              <span v-if="msg.role === 'assistant'" class="role-tag">AI助手</span>
            </div>
            <div class="message-bubble">{{ msg.content }}</div>
            <div class="message-time">{{ msg.created_at?.substring(11, 16) }}</div>
          </div>
          <!-- RAG 知识来源卡片 -->
          <div v-if="msg.role === 'assistant' && msg.ragSources?.length" class="rag-sources-card">
            <div class="rag-sources-header">
              <span>📚 参考知识</span>
              <span class="rag-sources-count">{{ msg.ragSources.length }} 条来源</span>
            </div>
            <div class="rag-sources-list">
              <div v-for="(src, si) in msg.ragSources" :key="si" class="rag-source-item">
                <div class="rag-source-title">{{ src.title }}</div>
                <div class="rag-source-summary">{{ src.summary }}</div>
                <div class="rag-source-meta">
                  <span class="rag-source-sim">相关度 {{ (src.similarity * 100).toFixed(0) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-if="thinking" class="message-item assistant">
          <div class="message-sender">小暖 <span class="role-tag">AI助手</span></div>
          <div class="message-bubble typing">正在思考中...</div>
        </div>
        <div v-if="!messages.length && !loading" class="empty-state">
          你好！有什么想聊的，随时告诉我 😊
        </div>
      </div>

      <div class="chat-input card">
        <textarea
          v-model="inputText"
          class="form-textarea"
          placeholder="说说你最近的心情或困扰..."
          rows="2"
          @keydown.enter.exact.prevent="handleSend"
        ></textarea>
        <button class="btn btn-primary send-btn" :disabled="!inputText.trim() || sending" @click="handleSend">
          {{ sending ? '发送中...' : '发送' }}
        </button>
      </div>

      <p class="disclaimer">AI回复仅供参考，不能替代专业心理咨询。如有严重困扰，请预约校内咨询师。</p>
    </main>
  </div>
</template>

<script setup>
/**
 * AI心理助手对话页面
 */
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAiSessions, getAiChatStatus, createAiSession, getAiMessages, sendAiMessage, deleteAiSession } from '../api'

const route = useRoute()
const router = useRouter()
const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)
const inputText = ref('')
const sending = ref(false)
const thinking = ref(false)
const loading = ref(true)
const ragActive = ref(false)
const messageBox = ref(null)

onMounted(() => init())

function normalizeMessages(list) {
  return (list || []).map((m) => ({
    ...m,
    ragSources: m.ragSources || m.rag_sources || [],
  }))
}

async function refreshRagStatus() {
  try {
    const res = await getAiChatStatus()
    ragActive.value = !!(res.data?.rag_ready || res.data?.rag_enabled)
  } catch (_) {
    /* 状态接口失败不影响聊天 */
  }
}

async function init() {
  loading.value = true
  try {
    await refreshRagStatus()
    const res = await getAiSessions()
    sessions.value = res.data || []
    const routeId = route.params.id ? Number(route.params.id) : null
    if (routeId && sessions.value.find(s => s.id === routeId)) {
      await switchSession(routeId)
    } else if (sessions.value.length) {
      await switchSession(sessions.value[0].id)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleNewSession() {
  try {
    const res = await createAiSession({ title: 'AI心理助手' })
    const id = res.data.session_id
    const listRes = await getAiSessions()
    sessions.value = listRes.data
    await switchSession(id)
  } catch (e) {
    alert(e.message)
  }
}

async function handleDelete(sessionId) {
  if (!confirm('确定要删除这个对话吗？删除后无法恢复。')) return
  try {
    await deleteAiSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      // 切换到第一个剩余会话，或清空
      if (sessions.value.length) {
        await switchSession(sessions.value[0].id)
      } else {
        currentSessionId.value = null
        messages.value = []
      }
    }
  } catch (e) {
    alert(e.message)
  }
}

async function switchSession(id) {
  currentSessionId.value = id
  router.replace(`/consultations/ai/${id}`)
  try {
    const res = await getAiMessages(id)
    messages.value = normalizeMessages(res.data)
    if (messages.value.some((m) => m.ragSources?.length)) {
      ragActive.value = true
    }
    scrollToBottom()
  } catch (e) {
    console.error(e)
  }
}

async function handleSend() {
  if (!inputText.value.trim() || sending.value) return
  if (!currentSessionId.value) {
    await handleNewSession()
    if (!currentSessionId.value) return
  }

  const content = inputText.value.trim()
  inputText.value = ''
  sending.value = true
  thinking.value = true

  // 乐观更新用户消息
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  })
  scrollToBottom()

  try {
    const res = await sendAiMessage(currentSessionId.value, { content })
    const sources = res.data.rag_sources || []
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: res.data.reply,
      ragSources: sources,
      created_at: new Date().toISOString(),
    })
    if (res.data.rag_used || sources.length) {
      ragActive.value = true
    }
    // 刷新会话列表（标题可能已更新）；不重拉消息，避免丢掉本轮来源展示
    const listRes = await getAiSessions()
    sessions.value = listRes.data
    scrollToBottom()
  } catch (e) {
    alert(e.message)
    // 重新加载消息
    const mRes = await getAiMessages(currentSessionId.value)
    messages.value = normalizeMessages(mRes.data)
  } finally {
    sending.value = false
    thinking.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.ai-chat-page {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
  height: calc(100vh - 64px);
}

.session-panel {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
}

.panel-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 8px 0 12px;
}

.back-link {
  font-size: 15px;
  color: var(--primary);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 4px;
}

.session-item:hover { background: #f0f4f8; }
.session-item.active {
  background: #e8f4f8;
  border: 1px solid var(--primary-light);
}

.session-icon { font-size: 24px; }

.session-title {
  display: block;
  font-size: 15px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 170px;
}

.session-time {
  font-size: 13px;
  color: var(--text-muted);
}

.session-delete-btn {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  opacity: 0;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
}

.session-delete-btn:hover {
  background: #e74c3c;
  color: #fff;
}

.empty-hint {
  padding: 20px;
  text-align: center;
  font-size: 15px;
  color: var(--text-muted);
}

.chat-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  margin-bottom: 0;
  border-radius: var(--radius) var(--radius) 0 0;
}

.ai-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #e8f4f8, #d4edda);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}

.chat-header h3 {
  font-size: 17px;
  font-weight: 600;
}

.chat-header p {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 2px;
}

.ai-badge {
  margin-left: auto;
  padding: 4px 12px;
  background: linear-gradient(135deg, #7b68c4, #9b8fd4);
  color: #fff;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.rag-badge {
  padding: 4px 12px;
  background: linear-gradient(135deg, #e8f4f8, #d4edf4);
  color: #456a5d;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  margin-left: 6px;
}

.rag-badge-off {
  background: #f0f0f0;
  color: #888;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.message-item {
  margin-bottom: 16px;
  max-width: 75%;
}

.message-item.mine {
  margin-left: auto;
  text-align: right;
}

.message-item.assistant .message-bubble {
  background: linear-gradient(135deg, #f0ebfa 0%, #e8f4f8 100%);
  border: 1px solid #d4c4ef;
  color: #3d3556;
  box-shadow: 0 2px 10px rgba(123, 104, 196, 0.1);
}

.message-item.assistant .message-bubble.typing {
  background: #f5f0fc;
  color: #8b7cb0;
  border: 1px dashed #d4c4ef;
}

.message-sender {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.role-tag {
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #f0ebfa;
  color: #7b68c4;
  font-size: 13px;
}

.message-bubble {
  display: inline-block;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--primary);
  color: #fff;
  font-size: 16px;
  line-height: 1.7;
  white-space: pre-wrap;
  text-align: left;
}

.message-item.mine .message-bubble {
  background: var(--primary);
  color: #fff;
}

.message-bubble.typing {
  font-style: italic;
}

.message-time {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* RAG 知识来源卡片 */
.rag-sources-card {
  margin-bottom: 16px;
  margin-left: 0;
  max-width: 75%;
  background: rgba(212, 241, 224, 0.3);
  border: 1px solid rgba(107, 168, 136, 0.25);
  border-radius: 10px;
  padding: 12px 16px;
  backdrop-filter: blur(8px);
}

.rag-sources-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
}

.rag-sources-count {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
}

.rag-sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rag-source-item {
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border-left: 3px solid #6ba888;
}

.rag-source-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.rag-source-summary {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rag-source-meta {
  margin-top: 4px;
  display: flex;
  gap: 10px;
}

.rag-source-sim {
  font-size: 11px;
  color: #6ba888;
  font-weight: 500;
  background: rgba(107, 168, 136, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 16px;
  border-radius: 0 0 var(--radius) var(--radius);
}

.chat-input .form-textarea {
  flex: 1;
  min-height: 48px;
  resize: none;
}

.send-btn {
  flex-shrink: 0;
  padding: 12px 24px;
}

.disclaimer {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 10px;
  padding-bottom: 8px;
}

@media (max-width: 900px) {
  .ai-chat-page {
    grid-template-columns: 1fr;
    height: auto;
  }
  .session-panel { max-height: 200px; }
}
</style>
