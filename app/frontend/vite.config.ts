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
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:9393',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        // 使用时间戳强制浏览器更新缓存
        entryFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        chunkFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        assetFileNames: `assets/[name]-[hash]-${Date.now()}.[ext]`,
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd', '@ant-design/icons'],
          charts: ['echarts', 'echarts-for-react'],
        },
      },
    },
  },
  esbuild: {
    // 生产环境移除console.log和debugger
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
    // 保留console.error和console.warn用于错误追踪
    pure: process.env.NODE_ENV === 'production' ? ['console.log', 'console.debug', 'console.info'] : [],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', 'echarts'],
  },
})