/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 设计系统色彩配置
        'background-main': 'rgb(250, 249, 245)',
        'background-secondary': 'rgb(245, 244, 237)',
        'background-card': 'rgb(255, 255, 255)',
        'button-disabled': 'rgb(228, 177, 160)',
        'button-active': 'rgb(201, 100, 66)',
        'function-selected': 'rgb(222, 235, 255)',
        'text-primary': 'rgb(29, 29, 31)',
        'text-secondary': 'rgb(117, 117, 117)',
      },
      boxShadow: {
        'input-card': '0 -4px 20px -2px rgba(0, 0, 0, 0.08), 0 -2px 8px -2px rgba(0, 0, 0, 0.04)',
        'floating': '0 8px 32px -8px rgba(0, 0, 0, 0.12), 0 2px 8px -2px rgba(0, 0, 0, 0.08)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'pulse-subtle': 'pulseSubtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}