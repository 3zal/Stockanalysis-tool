/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-primary': 'rgb(var(--bg) / <alpha-value>)',
        'bg-secondary': 'rgb(var(--surface) / <alpha-value>)',
        'bg-card': 'rgb(var(--surface) / <alpha-value>)',
        'bg-card-2': 'rgb(var(--surface-2) / <alpha-value>)',
        'bg-card-3': 'rgb(var(--surface-3) / <alpha-value>)',
        'border-subtle': 'rgb(var(--border) / <alpha-value>)',
        'border-active': 'rgb(var(--border-strong) / <alpha-value>)',
        'border-glow': 'rgb(var(--border-strong) / <alpha-value>)',

        'text-primary': 'rgb(var(--text) / <alpha-value>)',
        'text-secondary': 'rgb(var(--text-2) / <alpha-value>)',
        'text-tertiary': 'rgb(var(--text-3) / <alpha-value>)',
        'text-muted': 'rgb(var(--text-4) / <alpha-value>)',

        'accent-green': 'rgb(var(--green) / <alpha-value>)',
        'accent-green-bright': 'rgb(var(--green) / <alpha-value>)',
        'accent-green-dim': 'rgb(var(--green) / 0.1)',
        'accent-green-muted': 'rgb(var(--green) / 0.25)',
        'accent-red': 'rgb(var(--red) / <alpha-value>)',
        'accent-red-dim': 'rgb(var(--red) / 0.1)',
        'accent-amber': 'rgb(var(--yellow) / <alpha-value>)',
        'accent-amber-dim': 'rgb(var(--yellow) / 0.1)',

        'accent-blue': 'rgb(var(--text-2) / <alpha-value>)',
        'accent-blue-dim': 'rgb(var(--text-2) / 0.1)',
        'accent-purple': 'rgb(var(--text-2) / <alpha-value>)',

        'light-bg': '#FFFFFF',
        'light-card': '#FAFAFA',
        'light-border': '#E5E5E5',
        'light-text': '#000000',
        'light-text-2': '#3F3F46',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Fraunces', 'Instrument Serif', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        xl: '0.625rem',
        '2xl': '0.75rem',
        '3xl': '1rem',
        '4xl': '1.25rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slideUp 0.45s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in': 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        'scale-in': 'scaleIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        shimmer: 'shimmer 1.6s infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideIn: { from: { opacity: '0', transform: 'translateX(-6px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        scaleIn: { from: { opacity: '0', transform: 'scale(0.97)' }, to: { opacity: '1', transform: 'scale(1)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
      boxShadow: {
        card: '0 1px 2px rgb(var(--shadow) / 0.04)',
        'card-hover': '0 4px 16px rgb(var(--shadow) / 0.08)',
        'card-elevated': '0 12px 32px rgb(var(--shadow) / 0.12)',
        'glow-green': 'none',
        'glow-red': 'none',
        'glow-blue': 'none',
      },
    },
  },
  plugins: [],
}
