import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

/** 从多条 Network 地址里挑一条给其他电脑用的（跳过虚拟网卡） */
function pickLanUrl(urls) {
  if (!urls?.length) return urls
  const score = (url) => {
    try {
      const ip = new URL(url).hostname
      if (ip.startsWith('10.')) return 3
      if (/^192\.168\.(?!56\.|137\.)/.test(ip)) return 2 // 排除 VirtualBox / 热点虚拟段
      if (ip.startsWith('172.')) return 0 // Hyper-V / Docker / WSL 等
      return 1
    } catch {
      return -1
    }
  }
  return [urls.slice().sort((a, b) => score(b) - score(a))[0]]
}

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'print-one-lan-url',
      configureServer(server) {
        const original = server.printUrls.bind(server)
        server.printUrls = () => {
          if (server.resolvedUrls?.network) {
            server.resolvedUrls.network = pickLanUrl(server.resolvedUrls.network)
          }
          original()
        }
      }
    }
  ],
  server: {
    host: true, // 仍监听 0.0.0.0，本机 localhost 可用
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      // 代理后端静态媒体文件（放松训练音频/视频）
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
