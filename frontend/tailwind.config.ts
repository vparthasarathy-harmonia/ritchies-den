/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}", // Tailwind will scan your app, components, pages, etc.
  ],
  darkMode: 'class', // Enables manual theme switching using class="dark"
  theme: {
    extend: {
      // You can add custom colors, spacing, fonts, etc. here
    },
  },
  plugins: [],
};
