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
          bg: "#090b10",
          panel: "#0d1117",
          hover: "#131822",
          subtle: "#161b26",
          border: "#1c2333",
          borderHover: "#2a344d",
          borderActive: "#3b4866",
        },
        ink: {
          primary: "#f0f3f8",
          secondary: "#8b96a5",
          muted: "#556070",
          faint: "#384152",
        },
        metric: {
          blue: "#3b82f6",
          cyan: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
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
