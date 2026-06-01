/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b1220",
        surface: "#131c2e",
        "surface-2": "#1b2740",
        border: "#26324d",
        primary: "#3b82f6",
        bull: "#16a34a",
        bear: "#dc2626",
        muted: "#8b98b0",
      },
    },
  },
  plugins: [],
};
