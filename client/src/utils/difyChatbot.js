/**
 * Dify 嵌入式聊天助手
 * 配置见 client/.env：VITE_DIFY_TOKEN、VITE_DIFY_BASE_URL
 */

const CONFIG_KEY = 'difyChatbotConfig'

function getToken() {
  return import.meta.env.VITE_DIFY_TOKEN || 'QLtqFaRkAn8y8kjw'
}

function getBaseUrl() {
  return (import.meta.env.VITE_DIFY_BASE_URL || 'http://localhost').replace(/\/$/, '')
}

export function initDifyChatbot(options = {}) {
  const token = getToken()
  const baseUrl = getBaseUrl()

  window[CONFIG_KEY] = {
    token,
    baseUrl,
    inputs: options.inputs || {},
    systemVariables: options.systemVariables || {},
    userVariables: options.userVariables || {},
  }

  if (document.getElementById(token)) {
    return
  }

  const script = document.createElement('script')
  script.src = `${baseUrl}/embed.min.js`
  script.id = token
  script.defer = true
  document.body.appendChild(script)
}

/** 登录后传入当前用户信息，便于 Dify 工作流识别用户 */
export function syncDifyUser(user) {
  if (!window[CONFIG_KEY]) {
    return
  }
  if (!user) {
    window[CONFIG_KEY].userVariables = {}
    window[CONFIG_KEY].systemVariables = {}
    return
  }
  window[CONFIG_KEY].userVariables = {
    name: user.nickname || user.real_name || user.username || '访客',
    avatar_url: user.avatar || '',
  }
  window[CONFIG_KEY].systemVariables = {
    user_id: String(user.id),
    user_role: user.role || '',
  }
}

export function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}
