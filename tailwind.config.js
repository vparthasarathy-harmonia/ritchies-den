/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}", // Covers App Router structure
    "./pages/**/*.{js,ts,jsx,tsx}", // Optional: supports legacy pages if added
    "./components/**/*.{js,ts,jsx,tsx}", // Optional: for any shared UI components
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
