import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        obs: {
          bg: '#132D42',
          'bg-dark': '#0F1F2D',
          blue: '#0080FF',
          'blue-light': '#40BBFF',
          accent: '#2ca4ec',
          red: '#e03131',
        },
        signal: {
          green: '#2ecc71',
          yellow: '#f39c12',
          orange: '#e67e22',
          red: '#e74c3c',
          gray: '#95a5a6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'DejaVu Sans', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
