/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paper/Warm Theme Palette
        paper: {
          white: '#FFFFFF',
          cream: '#FFFDF9',
          warm: '#FFF9F5',
          soft: '#FEFCFA',
        },
        // Gradient Colors
        gradient: {
          peach: '#FAD4C0',
          salmon: '#F8C8B8',
          pink: '#F5B8C8',
          rose: '#E8C4D8',
          lavender: '#D4C4E8',
          violet: '#C8B8E8',
        },
        // Primary accent - Deep purple (like Sudowrite's purple)
        primary: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
        },
        // Background Colors - Light Theme
        bg: {
          main: '#FFFDF9',
          sidebar: '#FFFFFF',
          hover: 'rgba(139, 92, 246, 0.08)',
          input: '#FFFFFF',
          card: '#FFFFFF',
        },
        // Glass Effects - Light tinted
        glass: {
          light: 'rgba(255, 255, 255, 0.7)',
          border: 'rgba(0, 0, 0, 0.08)',
          shadow: 'rgba(0, 0, 0, 0.1)',
        },
        // Accent Colors
        accent: {
          primary: '#7C3AED',
          hover: '#8B5CF6',
          secondary: '#6D28D9',
          muted: '#A78BFA',
        },
        // Text Colors - Dark for readability
        text: {
          primary: '#1A1A2E',
          secondary: '#4A4A5A',
          muted: '#8A8A9A',
          light: '#B0B0C0',
        },
        // Border Colors
        border: {
          DEFAULT: 'rgba(0, 0, 0, 0.08)',
          light: 'rgba(0, 0, 0, 0.04)',
          accent: 'rgba(139, 92, 246, 0.3)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'editor': ['18px', '1.8'],
      },
      spacing: {
        'toolbar': '60px',
        'sidebar': '280px',
      },
      borderRadius: {
        'paper': '12px',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'paper': '0 2px 8px rgba(0, 0, 0, 0.06), 0 4px 20px rgba(0, 0, 0, 0.04)',
        'paper-hover': '0 4px 16px rgba(0, 0, 0, 0.08), 0 8px 32px rgba(0, 0, 0, 0.06)',
        'paper-lg': '0 8px 30px rgba(0, 0, 0, 0.08), 0 16px 60px rgba(0, 0, 0, 0.05)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.04)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08), 0 8px 24px rgba(0, 0, 0, 0.06)',
        'inner-soft': 'inset 0 2px 4px rgba(0, 0, 0, 0.02)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'float': 'float 6s ease-in-out infinite',
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
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}
