/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Electric Violet Palette
        violet: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6', // Electric Violet - Primary
          600: '#7C3AED',
          700: '#6D28D9', // Deep Indigo
          800: '#5B21B6',
          900: '#4C1D95',
          950: '#2E1065',
        },
        // Background Colors - Pure Black Theme
        bg: {
          main: 'rgba(0, 0, 0, 0.95)',
          sidebar: 'rgba(5, 5, 8, 0.98)',
          hover: 'rgba(139, 92, 246, 0.1)',
          input: 'rgba(10, 10, 15, 0.95)',
          card: 'rgba(10, 10, 15, 0.8)',
        },
        // Glass Effects - Violet tinted
        glass: {
          light: 'rgba(139, 92, 246, 0.05)',
          border: 'rgba(255, 255, 255, 0.1)',
          shadow: 'rgba(0, 0, 0, 0.8)',
        },
        // Accent Colors - Electric Violet
        accent: {
          primary: '#8B5CF6',
          hover: '#A78BFA',
          secondary: '#6D28D9',
          muted: '#4C1D95',
        },
        // Text Colors - Clean whites and grays
        text: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
          muted: '#64748B',
        },
        // Border Colors - Subtle violet tint
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.1)',
          light: 'rgba(255, 255, 255, 0.05)',
          accent: 'rgba(139, 92, 246, 0.3)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'SF Pro Display', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
      },
      fontSize: {
        'editor': ['18px', '1.8'],
      },
      spacing: {
        'toolbar': '60px',
        'sidebar': '280px',
      },
      backdropBlur: {
        'glass': '20px',
        'heavy': '40px',
      },
      borderRadius: {
        'glass': '16px',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(139, 92, 246, 0.2)' },
          '50%': { boxShadow: '0 0 40px rgba(139, 92, 246, 0.4)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(139, 92, 246, 0.3)' },
          '100%': { boxShadow: '0 0 40px rgba(139, 92, 246, 0.6)' },
        },
      },
      boxShadow: {
        'glow': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glow-lg': '0 0 40px rgba(139, 92, 246, 0.4)',
        'glow-xl': '0 0 60px rgba(139, 92, 246, 0.5)',
        'inner-glow': 'inset 0 0 20px rgba(139, 92, 246, 0.1)',
      },
      backgroundImage: {
        'shimmer': 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.2), transparent)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      }
    },
  },
  plugins: [],
}
