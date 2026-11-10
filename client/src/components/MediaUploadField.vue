<template>
  <div class="media-upload">
    <label v-if="label" class="upload-label">{{ label }}</label>
    <div v-if="modelValue.length < MAX_MEDIA_COUNT" class="upload-area">
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept="image/jpeg,image/png,image/gif,image/webp,video/mp4,video/webm,video/quicktime,.m4v"
        class="file-input"
        @change="handleFileSelect"
      />
      <button type="button" class="btn btn-outline" :disabled="uploading" @click="triggerFileInput">
        {{ uploading ? '上传中...' : buttonText }}
      </button>
      <span class="upload-hint">
        图片 ≤10MB，视频 ≤50MB，最多 {{ MAX_MEDIA_COUNT }} 个（已选 {{ modelValue.length }} 个）
      </span>
    </div>
    <div v-if="modelValue.length" class="media-preview-grid">
      <div v-for="(item, index) in modelValue" :key="item.media_url" class="preview-item">
        <img v-if="item.media_type === 'image'" :src="item.media_url" alt="预览" class="preview-image" />
        <video v-else :src="item.media_url" controls class="preview-video" />
        <button type="button" class="btn btn-sm btn-danger remove-item" @click="removeItem(index)">移除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { MAX_MEDIA_COUNT } from '../utils/media'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  uploadFn: { type: Function, required: true },
  label: { type: String, default: '' },
  buttonText: { type: String, default: '📷 选择照片/视频' },
})

const emit = defineEmits(['update:modelValue', 'error'])

const uploading = ref(false)
const fileInputRef = ref(null)

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function handleFileSelect(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  const remaining = MAX_MEDIA_COUNT - props.modelValue.length
  if (remaining <= 0) {
    emit('error', `最多上传 ${MAX_MEDIA_COUNT} 个文件`)
    return
  }

  const toUpload = files.slice(0, remaining)
  if (files.length > remaining) {
    emit('error', `最多还能上传 ${remaining} 个文件，已自动忽略多余文件`)
  }

  uploading.value = true
  const next = [...props.modelValue]
  try {
    for (const file of toUpload) {
      const res = await props.uploadFn(file)
      next.push({
        media_url: res.data.media_url,
        media_type: res.data.media_type,
      })
    }
    emit('update:modelValue', next)
  } catch (e) {
    emit('error', e.message)
  } finally {
    uploading.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

function removeItem(index) {
  const next = [...props.modelValue]
  next.splice(index, 1)
  emit('update:modelValue', next)
}
</script>

<style scoped>
.media-upload { margin-bottom: 16px; }
.upload-label {
  display: block;
  font-size: 15px;
  color: var(--text-muted, var(--text-secondary));
  margin-bottom: 8px;
}
.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.file-input { display: none; }
.btn-outline {
  background: #fff;
  border: 1px dashed var(--primary, #4a90a4);
  color: var(--primary, #4a90a4);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
}
.btn-outline:disabled { opacity: 0.6; cursor: not-allowed; }
.upload-hint { font-size: 14px; color: var(--text-muted, var(--text-muted)); }
.media-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.preview-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: #eceff2;
}
.preview-image,
.preview-video {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}
.remove-item {
  position: absolute;
  top: 6px;
  right: 6px;
}
</style>
