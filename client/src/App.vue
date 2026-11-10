<template>
  <router-view />
</template>

<script setup>
/**
 * 根组件
 * 作为路由视图容器
 */
import { onMounted, onUnmounted } from 'vue'
import { initDifyChatbot, readStoredUser, syncDifyUser } from './utils/difyChatbot'

function refreshDifyUser() {
  syncDifyUser(readStoredUser())
}

onMounted(() => {
  initDifyChatbot()
  refreshDifyUser()
  window.addEventListener('user-updated', refreshDifyUser)
})

onUnmounted(() => {
  window.removeEventListener('user-updated', refreshDifyUser)
})
</script>
