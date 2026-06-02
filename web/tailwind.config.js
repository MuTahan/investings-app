/** @type {import('tailwindcss').Config} */
const withVar = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: withVar("bg"),
        surface: withVar("surface"),
        "surface-2": withVar("surface-2"),
        "surface-3": withVar("surface-3"),
        border: withVar("border"),
        "border-strong": withVar("border-strong"),
        fg: withVar("fg"),
        "fg-soft": withVar("fg-soft"),
        muted: withVar("muted"),
        faint: withVar("faint"),
        primary: withVar("primary"),
        "primary-hover": withVar("primary-hover"),
        "primary-fg": withVar("primary-fg"),
        accent: withVar("primary"),
        bull: withVar("bull"),
        bear: withVar("bear"),
        warn: withVar("warn"),
        info: withVar("info"),
      },
      fontFamily: {
        sans: [
          "Inter var",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 3px 0 rgb(0 0 0 / 0.06)",
        lift: "0 4px 12px -2px rgb(0 0 0 / 0.10), 0 2px 6px -2px rgb(0 0 0 / 0.08)",
        glow: "0 0 0 1px rgb(var(--primary) / 0.35), 0 6px 20px -6px rgb(var(--primary) / 0.45)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out both",
        "slide-up": "slide-up 0.28s cubic-bezier(0.22, 1, 0.36, 1) both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};
