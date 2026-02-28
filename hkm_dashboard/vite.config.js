import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: '/assets/hkm/hkm-dashboard/',
  build: {
    outDir: '../hkm/public/hkm-dashboard',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'js/[name].bundle.[hash].js',
        chunkFileNames: 'js/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name].bundle.[hash].[ext]';
          }
          return 'assets/[name].[hash].[ext]';
        }
      }
    }
  },
  server: {
    port: 8081,
    proxy: {
      '^/api': {
        target: 'http://hkmjerp.in',
        changeOrigin: true,
        secure: false
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});

