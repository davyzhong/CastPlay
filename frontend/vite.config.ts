import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { resolve } from 'path'

// 获取构建时环境变量
const REGISTRATION_CODE = process.env.REGISTRATION_CODE || '';

export default defineConfig({
  plugins: [react()],
  // 使用相对路径，支持 Android WebView 本地文件加载
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  // 构建时环境变量定义
  define: {
    'import.meta.env.VITE_REGISTRATION_CODE': JSON.stringify(REGISTRATION_CODE),
  },
  // 多页面应用配置
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        player: resolve(__dirname, 'player.html'),
      },
    },
  },
  server: {
    port: 3000,
    strictPort: true,  // 端口被占用时报错而不是自动切换
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      },
      '/media': {
        target: 'http://localhost:8001',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true
      }
    }
  }
})
