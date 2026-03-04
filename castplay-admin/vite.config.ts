import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Code Splitting 配置
    rollupOptions: {
      output: {
        manualChunks: {
          // React 核心库
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Ant Design UI 库
          'antd-vendor': ['antd', '@ant-design/icons'],
          // 工具库
          'utils-vendor': ['axios', 'dayjs', 'zustand'],
          // 拖拽库
          'dnd-vendor': ['@dnd-kit/core', '@dnd-kit/sortable', '@dnd-kit/utilities'],
        },
      },
    },
    // 调整 chunk 大小警告阈值
    chunkSizeWarningLimit: 600,
  },
})
