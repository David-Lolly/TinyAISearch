import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' 

export default defineConfig({
  plugins: [vue()],
  resolve: { 
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // 关键改动：只保留一个 /api 规则
      '/api': {
        target: 'http://localhost:5000', // 你的后端地址
        changeOrigin: true,
        // 关键改动：重写路径，去掉 /api 前缀
        // 这样，发往后端的请求就是 /login, /sessions 等，而不是 /api/login
        // rewrite: (path) => path.replace(/^\/api/, ''),
        rewrite: (path) => path.replace(/^\/backend/, ''),
      },
      // 其他代理规则可以继续添加
      '/login': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/register': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/session': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/sessions': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/search': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },

    },
  },
})