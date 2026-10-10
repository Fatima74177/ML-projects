/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        eefbg: "var(--eef-bg)",
        eefpanel: "var(--eef-panel)",
        eefborder: "var(--eef-border)",
      },
    },
  },
  plugins: [],
}
