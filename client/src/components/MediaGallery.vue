<template>
  <div v-if="items.length" class="media-gallery" :class="size">
    <div v-for="(item, index) in items" :key="item.media_url + index" class="gallery-item">
      <img v-if="item.media_type === 'image'" :src="item.media_url" :alt="alt" class="gallery-image" />
      <video v-else :src="item.media_url" controls class="gallery-video" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getMediaList } from '../utils/media'

const props = defineProps({
  record: { type: Object, default: null },
  list: { type: Array, default: null },
  alt: { type: String, default: '媒体' },
  size: { type: String, default: 'md' },
})

const items = computed(() => {
  if (props.list) return props.list
  return getMediaList(props.record)
})
</script>

<style scoped>
.media-gallery {
  display: grid;
  gap: 12px;
}
.media-gallery.md {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}
.media-gallery.lg {
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}
.gallery-item {
  border-radius: 12px;
  overflow: hidden;
  background: #eceff2;
  border: 1px solid rgba(69, 106, 93, 0.08);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(30, 45, 61, 0.06));
}
.gallery-image,
.gallery-video {
  width: 100%;
  display: block;
  object-fit: cover;
}
.media-gallery.md .gallery-image,
.media-gallery.md .gallery-video {
  max-height: 240px;
}
.media-gallery.lg .gallery-image,
.media-gallery.lg .gallery-video {
  max-height: 320px;
}
</style>
