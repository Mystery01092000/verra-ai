import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    '../../packages/design-system/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        accent: '#5566FF',
        'accent-600': '#4F46E5',
        'accent-700': '#3A33C9',
        periwinkle: '#8A92FF',
        'periwinkle-soft': '#E6E8FF',
        ink: '#111114',
        'ink-secondary': '#5B5B66',
        muted: '#8A8A95',
        line: '#E8E8EC',
        cream: '#F5F5F5',
        ok: '#1FBF75',
        warn: '#E5A33B',
        danger: '#E5484D',
      },
      fontFamily: {
        display: ['Archivo', 'sans-serif'],
        serif: ['Fraunces', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '18px',
        'card-lg': '22px',
        btn: '9px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(17,17,20,.04), 0 12px 32px rgba(17,17,20,.06)',
        lg: '0 24px 60px rgba(40,40,90,.18)',
        glow: '0 0 0 1px rgba(85,102,255,.25), 0 18px 50px rgba(85,102,255,.18)',
      },
    },
  },
  plugins: [],
};

export default config;
