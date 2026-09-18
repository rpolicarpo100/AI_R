/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        surface: "#11111b",
        surface2: "#181825",
        border: "#1e1e2e",
        accent: "#6366f1",
      }
    },
  },
  plugins: [],
}
