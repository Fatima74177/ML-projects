import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/static/react/',
  build: {
    outDir: '../static/react',
    emptyOutDir: true,
    rollupOptions: {
      input: './index.html',
      output: {
        entryFileNames: 'dashboard-react.js',
        assetFileNames: 'dashboard-react.[ext]',
      },
    },
  },
});
