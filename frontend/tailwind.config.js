/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        blue: {
          '400': '#2563eb',
          '500': '#2563eb', 
          '600': '#1d4ed8', 
        },
      },
    },
  },
  plugins: [],
}