/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Theme Base Colors
        dark: {
          950: '#0A0A0F',
          900: '#0F0F14',
          850: '#121218',
          800: '#16161D',
          750: '#1A1A22',
          700: '#1E1E28',
          600: '#252530',
          500: '#2D2D3A',
          400: '#3A3A4A',
        },
        // Gold Palette - Luxurious Gold Tones
        gold: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
          // Special gold variants
          bright: '#FFD700',
          rich: '#D4AF37',
          amber: '#FFBF00',
          pale: '#EAC67A',
          deep: '#B8860B',
          muted: '#C9A227',
          // Soft/warm gold variants (less intense)
          soft: '#E8D5A3',
          warm: '#D4C4A0',
          cream: '#F5E6C8',
          light: '#F0E4C9',
        },
        // Primary accent - Gold
        primary: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Background Colors - Dark Theme
        bg: {
          main: '#0A0A0F',
          sidebar: '#0F0F14',
          card: '#16161D',
          hover: 'rgba(212, 175, 55, 0.08)',
          input: '#1A1A22',
          elevated: '#1E1E28',
        },
        // Glass Effects - Dark with gold tint
        glass: {
          dark: 'rgba(15, 15, 20, 0.85)',
          light: 'rgba(212, 175, 55, 0.05)',
          border: 'rgba(212, 175, 55, 0.15)',
          shadow: 'rgba(0, 0, 0, 0.5)',
        },
        // Accent Colors - Gold variants
        accent: {
          primary: '#D4AF37',
          hover: '#E8C252',
          secondary: '#B8860B',
          muted: '#8B7355',
        },
        // Text Colors - Light for dark theme (ensure good visibility)
        text: {
          primary: '#F5F5F4',
          secondary: '#E5E5E5',
          muted: '#A1A1AA',
          light: '#71717A',
          gold: '#E8D5A3',
        },
        // Border Colors
        border: {
          DEFAULT: 'rgba(212, 175, 55, 0.15)',
          light: 'rgba(212, 175, 55, 0.08)',
          accent: 'rgba(212, 175, 55, 0.4)',
          gold: 'rgba(212, 175, 55, 0.3)',
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
        'gold-sm': '0 2px 8px rgba(212, 175, 55, 0.1)',
        'gold': '0 4px 20px rgba(212, 175, 55, 0.15)',
        'gold-lg': '0 8px 40px rgba(212, 175, 55, 0.2)',
        'gold-glow': '0 0 30px rgba(212, 175, 55, 0.3)',
        'dark': '0 4px 20px rgba(0, 0, 0, 0.4)',
        'dark-lg': '0 8px 40px rgba(0, 0, 0, 0.5)',
        'inner-gold': 'inset 0 1px 2px rgba(212, 175, 55, 0.1)',
        'card': '0 4px 20px rgba(0, 0, 0, 0.3), 0 0 1px rgba(212, 175, 55, 0.2)',
        'card-hover': '0 8px 30px rgba(0, 0, 0, 0.4), 0 0 20px rgba(212, 175, 55, 0.15)',
      },
      backgroundImage: {
        'gold-gradient': 'linear-gradient(135deg, #D4AF37 0%, #F4CF47 50%, #D4AF37 100%)',
        'gold-gradient-subtle': 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(244, 207, 71, 0.1) 100%)',
        'dark-gradient': 'linear-gradient(180deg, #0F0F14 0%, #0A0A0F 100%)',
        'dark-radial': 'radial-gradient(ellipse at center, #1A1A22 0%, #0A0A0F 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-gold': 'pulseGold 2s ease-in-out infinite',
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
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseGold: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(212, 175, 55, 0.2)' },
          '100%': { boxShadow: '0 0 30px rgba(212, 175, 55, 0.4)' },
        },
      },
    },
  },
  plugins: [],
}
