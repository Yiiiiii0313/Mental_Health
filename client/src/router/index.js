/**
 * Vue Router 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { public: true } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPassword.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('../views/Home.vue') },
      { path: 'scales', name: 'Scales', component: () => import('../views/ScaleList.vue') },
      { path: 'scales/records/:id', name: 'ScaleRecordDetail', component: () => import('../views/ScaleRecordDetail.vue') },
      { path: 'scales/:id', name: 'ScaleTest', component: () => import('../views/ScaleTest.vue') },
      { path: 'appointments', name: 'Appointments', component: () => import('../views/Appointment.vue') },
      { path: 'counselors/:id', name: 'CounselorDetail', component: () => import('../views/CounselorDetail.vue') },
      { path: 'articles', name: 'Articles', component: () => import('../views/Articles.vue') },
      { path: 'articles/:id', name: 'ArticleDetail', component: () => import('../views/ArticleDetail.vue') },
      { path: 'announcements/:id', name: 'AnnouncementDetail', component: () => import('../views/AnnouncementDetail.vue') },
      { path: 'mood', name: 'Mood', component: () => import('../views/MoodDiary.vue') },
      { path: 'mood/day/:date', name: 'MoodDayDetail', component: () => import('../views/MoodDayDetail.vue') },
      { path: 'consultations', name: 'Consultations', component: () => import('../views/Consultation.vue') },
      { path: 'consultations/ai', name: 'AiChat', component: () => import('../views/AiChat.vue') },
      { path: 'consultations/ai/:id', name: 'AiChatSession', component: () => import('../views/AiChat.vue') },
      { path: 'consultations/:id', name: 'ConsultationChat', component: () => import('../views/ConsultationChat.vue') },
      { path: 'relaxation', name: 'Relaxation', component: () => import('../views/Relaxation.vue') },
      { path: 'relaxation/:id', name: 'RelaxationDetail', component: () => import('../views/RelaxationDetail.vue') },
      { path: 'games', name: 'MiniGames', component: () => import('../views/MiniGames.vue') },
      { path: 'games/:slug', name: 'MiniGamePlay', component: () => import('../views/MiniGamePlay.vue') },
      { path: 'tree-hole', name: 'TreeHole', component: () => import('../views/TreeHole.vue') },
      { path: 'tree-hole/:id', name: 'TreeHoleDetail', component: () => import('../views/TreeHoleDetail.vue') },
      { path: 'notifications', name: 'Notifications', component: () => import('../views/Notifications.vue') },
      { path: 'profile', name: 'Profile', component: () => import('../views/Profile.vue') },
      { path: 'admin', name: 'Admin', component: () => import('../views/admin/Dashboard.vue'), meta: { role: 'admin' } },
      { path: 'admin/users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { role: 'admin' } },
      { path: 'admin/students', name: 'AdminStudents', component: () => import('../views/admin/Students.vue'), meta: { role: 'admin' } },
      { path: 'admin/agent', name: 'AdminAgent', component: () => import('../views/admin/AgentCollaborate.vue'), meta: { role: 'admin' } },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  if (!to.meta.public && !token) next('/login')
  else if (to.meta.role && user?.role !== to.meta.role) next('/home')
  else next()
})

export default router
