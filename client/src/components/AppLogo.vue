<template>
  <img
    :src="src"
    :alt="alt"
    class="app-logo"
    :class="[`size-${size}`, { mark: mark }]"
    draggable="false"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'md', // sm | md | lg | xl
  },
  mark: {
    type: Boolean,
    default: false,
  },
  alt: {
    type: String,
    default: '心屿',
  },
})

// 圆形透明底 logo（原图线条保留）
const src = computed(() => (props.mark ? '/favicon.png?v=6' : '/logo.png?v=6'))
</script>

<style scoped>
.app-logo {
  display: block;
  object-fit: contain;
  user-select: none;
  flex-shrink: 0;
}

.app-logo:not(.mark) {
  margin-left: auto;
  margin-right: auto;
}

.size-sm { width: 48px; height: 48px; }
.size-md { width: 72px; height: 72px; }
.size-lg { width: 140px; height: 140px; }
.size-xl { width: 220px; height: 220px; }

.mark.size-sm { width: 44px; height: 44px; }
.mark.size-md { width: 56px; height: 56px; }
</style>
