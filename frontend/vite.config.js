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
      '/backend': {
        target: 'http://localhost:5000', // 你的后端地址
        changeOrigin: true,
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