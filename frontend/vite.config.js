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
      
      '/api': {
        target: 'http://localhost:5000', 
        changeOrigin: true, 
        
        
      },
      
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