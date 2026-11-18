/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#f4f6f9",
          panel: "#ffffff",
          hover: "#f8fafc",
          subtle: "#f1f5f9",
          border: "#e2e8f0",
          borderHover: "#cbd5e1",
          borderActive: "#94a3b8",
        },
        ink: {
          primary: "#0f172a",
          secondary: "#475569",
          muted: "#94a3b8",
          faint: "#cbd5e1",
        },
        metric: {
          blue: "#2563eb",
          cyan: "#0891b2",
          emerald: "#059669",
          amber: "#d97706",
          rose: "#e11d48",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: [
          '"JetBrains Mono"',
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
