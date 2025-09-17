/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../**/templates/**/*.html',
    '../theme/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#4F46E5',
        'secondary': '#10B981',
        'success': '#059669',
        'danger': '#DC2626',
        'warning': '#F59E0B',
        'info': '#3B82F6',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
