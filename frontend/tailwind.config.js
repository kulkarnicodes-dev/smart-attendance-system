/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['"Instrument Sans"', 'system-ui', 'sans-serif'] },
      colors: {
        ink: { DEFAULT: '#12232E', soft: '#3B505D', mute: '#6B7F8B' },
        paper: { DEFAULT: '#F1F5F7', card: '#FFFFFF', line: '#DCE4E9' },
        brand: { DEFAULT: '#0E7C7B', dark: '#0A5F5E', tint: '#DDF1F0' },
        signal: { amber: '#C77D0A', red: '#C0392B', green: '#1E8E5A' },
      },
    },
  },
  plugins: [],
}
