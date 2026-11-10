export const MAX_MEDIA_COUNT = 9

/** 从记录中取出媒体列表（兼容旧单文件字段） */
export function getMediaList(item) {
  if (item?.media_list?.length) return item.media_list
  if (item?.media_url) {
    return [{ media_url: item.media_url, media_type: item.media_type }]
  }
  return []
}

/** 媒体数量提示文案 */
export function mediaCountLabel(item) {
  const count = getMediaList(item).length
  if (!count) return ''
  const images = getMediaList(item).filter(m => m.media_type === 'image').length
  const videos = count - images
  const parts = []
  if (images) parts.push(`${images} 张图片`)
  if (videos) parts.push(`${videos} 个视频`)
  return parts.join('、')
}
