import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // react(): JSX and fast refresh (the page updates on save without a reload).
  // tailwindcss(): scans our files for class names like "text-green-700"
  // and generates only the CSS we actually use.
  plugins: [react(), tailwindcss()],
})
