/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#7F77DD',
          50: '#F0EEFB',
          100: '#E0DCF7',
          200: '#C1B9EF',
          300: '#A296E7',
          400: '#8373DF',
          500: '#7F77DD',
          600: '#5A50C9',
          700: '#433BA3',
          800: '#2F2A74',
          900: '#1C1945',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
