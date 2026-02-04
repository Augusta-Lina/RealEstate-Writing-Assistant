/**
 * Vite Configuration
 * ==================
 * 
 * Vite is a modern build tool that's MUCH faster than Create React App.
 * It uses native ES modules for instant hot module replacement (HMR).
 * 
 * This file configures how Vite builds and serves your app.
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // Plugins extend Vite's functionality
  plugins: [
    react()  // Enables React support (JSX, Fast Refresh, etc.)
  ],
  
  // Development server settings
  server: {
    port: 5173,  // Default Vite port
    open: true,  // Auto-open browser when you run 'npm run dev'
  },
  
  // Build settings (for production)
  build: {
    outDir: 'dist',  // Output directory for production build
  }
})
