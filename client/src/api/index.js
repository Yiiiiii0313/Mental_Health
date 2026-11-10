/**
 * API 接口定义
 */
import request from './request'

// ========== 认证相关 ==========
export const login = (data) => request.post('/auth/login', data)
export const register = (data) => request.post('/auth/register', data)
export const verifyStudent = (data) => request.post('/auth/verify-student', data)
export const getSecurityQuestions = () => request.get('/auth/security-questions')
export const sendResetCode = (data) => request.post('/auth/forgot-password/send-code', data)
export const resetPasswordByEmail = (data) => request.post('/auth/forgot-password/reset-by-email', data)
export const getSecurityQuestion = (username) => request.get('/auth/forgot-password/question', { params: { username } })
export const resetPasswordByQuestion = (data) => request.post('/auth/forgot-password/reset-by-question', data)
export const getProfile = () => request.get('/auth/profile')
export const updateProfile = (data) => request.put('/auth/profile', data)
export const uploadAvatar = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/auth/avatar/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}
export const changePassword = (data) => request.put('/auth/password', data)

// ========== 公告相关 ==========
export const getAnnouncements = (params) => request.get('/announcements', { params })
export const getAnnouncement = (id) => request.get(`/announcements/${id}`)

// ========== 文章相关 ==========
export const getArticles = (params) => request.get('/articles', { params })
export const getArticle = (id) => request.get(`/articles/${id}`)
export const likeArticle = (id) => request.post(`/articles/${id}/like`)
export const unlikeArticle = (id) => request.delete(`/articles/${id}/like`)
export const favoriteArticle = (id) => request.post(`/articles/${id}/favorite`)
export const unfavoriteArticle = (id) => request.delete(`/articles/${id}/favorite`)

// ========== 预约相关 ==========
export const getCounselors = () => request.get('/appointments/counselors')
export const getCounselor = (id) => request.get(`/appointments/counselors/${id}`)
export const getTimeSlots = () => request.get('/appointments/time-slots')
export const getAppointments = (params) => request.get('/appointments', { params })
export const createAppointment = (data) => request.post('/appointments', data)
export const updateAppointmentStatus = (id, data) => request.put(`/appointments/${id}/status`, data)
export const cancelAppointment = (id) => request.delete(`/appointments/${id}`)

// ========== 量表相关 ==========
export const getScales = () => request.get('/scales')
export const getScale = (id) => request.get(`/scales/${id}`)
export const submitScale = (id, data) => request.post(`/scales/${id}/submit`, data)
export const getScaleRecords = (params) => request.get('/scales/records', { params })
export const getScaleRecord = (id) => request.get(`/scales/records/${id}`)
export const getScaleTrends = (params) => request.get('/scales/trends', { params })

// ========== 健康洞察 ==========
export const getRiskInsight = () => request.get('/insight/risk')

// ========== 心情日记 ==========
export const getMoodLabels = () => request.get('/mood/labels')
export const getMoodDiaries = (params) => request.get('/mood', { params })
export const createMoodDiary = (data) => request.post('/mood', data)
export const uploadMoodMedia = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/mood/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}
export const deleteMoodDiary = (id) => request.delete(`/mood/${id}`)
export const getMoodStats = () => request.get('/mood/stats')
export const getMoodCalendar = (params) => request.get('/mood/calendar', { params })
export const getMoodByDate = (date) => request.get('/mood/by-date', { params: { date } })

// ========== 在线咨询 ==========
export const getConsultations = (params) => request.get('/consultations', { params })
export const createConsultation = (data) => request.post('/consultations', data)
export const getMessages = (id) => request.get(`/consultations/${id}/messages`)
export const sendMessage = (id, data) => request.post(`/consultations/${id}/messages`, data)
export const closeConsultation = (id) => request.put(`/consultations/${id}/close`)

// ========== AI心理助手 ==========
export const getAiSessions = () => request.get('/ai-chat/sessions')
export const getAiChatStatus = () => request.get('/ai-chat/status')
export const createAiSession = (data) => request.post('/ai-chat/sessions', data)
export const getAiMessages = (id) => request.get(`/ai-chat/sessions/${id}/messages`)
export const sendAiMessage = (id, data) => request.post(`/ai-chat/sessions/${id}/messages`, data, { timeout: 120000 })
export const deleteAiSession = (id) => request.delete(`/ai-chat/sessions/${id}`)

// ========== 放松训练 ==========
export const getRelaxationAudios = (params) => request.get('/relaxation/audios', { params })
export const getRelaxationAudio = (id) => request.get(`/relaxation/audios/${id}`)
export const likeRelaxation = (id) => request.post(`/relaxation/audios/${id}/like`)
export const unlikeRelaxation = (id) => request.delete(`/relaxation/audios/${id}/like`)
export const favoriteRelaxation = (id) => request.post(`/relaxation/audios/${id}/favorite`)
export const unfavoriteRelaxation = (id) => request.delete(`/relaxation/audios/${id}/favorite`)

// ========== 匿名树洞 ==========
export const getTreeHolePosts = (params) => request.get('/tree-hole', { params })
export const getTreeHolePost = (id) => request.get(`/tree-hole/${id}`)
export const createTreeHolePost = (data) => request.post('/tree-hole', data)
export const deleteTreeHolePost = (id) => request.delete(`/tree-hole/${id}`)
export const uploadTreeHoleMedia = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/tree-hole/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}
export const getTreeHoleReplies = (id) => request.get(`/tree-hole/${id}/replies`)
export const replyTreeHole = (id, data) => request.post(`/tree-hole/${id}/replies`, data)
export const deleteTreeHoleReply = (postId, replyId) => request.delete(`/tree-hole/${postId}/replies/${replyId}`)

// ========== 消息通知 ==========
export const getNotifications = (params) => request.get('/notifications', { params })
export const getUnreadCount = () => request.get('/notifications/unread-count')
export const markNotificationRead = (id) => request.put(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => request.put('/notifications/read-all')
export const deleteNotification = (id) => request.delete(`/notifications/${id}`)

// ========== 管理后台 ==========
export const getDashboard = () => request.get('/admin/dashboard')
export const getStudentRegistry = (params) => request.get('/admin/students', { params })
export const createStudentRegistry = (data) => request.post('/admin/students', data)
export const getUsers = (params) => request.get('/admin/users', { params })
export const createUser = (data) => request.post('/admin/users', data)
export const toggleUserStatus = (id, data) => request.put(`/admin/users/${id}/status`, data)
export const createAnnouncement = (data) => request.post('/admin/announcements', data)
export const deleteAnnouncement = (id) => request.delete(`/admin/announcements/${id}`)
export const createArticle = (data) => request.post('/admin/articles', data)
export const deleteArticle = (id) => request.delete(`/admin/articles/${id}`)

/** 多智能体协作（管理员） */
export const getAgentDatasets = () => request.get('/admin/agent/datasets')
export const runAgentReport = (data) => request.post('/admin/agent/run', data, { timeout: 180000 })

/** 导出 CSV 报表（管理员） */
export async function exportData(type) {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/admin/export/${type}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) throw new Error('导出失败')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${type}_export.csv`
  a.click()
  URL.revokeObjectURL(url)
}
