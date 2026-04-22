import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0A84FF",
          dark: "#0066CC",
          soft: "rgba(10,132,255,0.12)",
          softer: "rgba(10,132,255,0.05)",
        },
        success: {
          DEFAULT: "#22C55E",
          bg: "rgba(34,197,94,0.10)",
          border: "rgba(34,197,94,0.18)",
        },
        danger: {
          DEFAULT: "#EF4444",
          bg: "rgba(239,68,68,0.10)",
          border: "rgba(239,68,68,0.18)",
        },
        warning: {
          DEFAULT: "#F59E0B",
          bg: "rgba(245,158,11,0.10)",
          border: "rgba(245,158,11,0.18)",
        },
        surface: {
          bg: "#F4F7FB",
          "bg-alt": "#EEF3F8",
          card: "#FFFFFF",
          muted: "#F8FAFC",
        },
        ink: {
          DEFAULT: "#0F172A",
          muted: "#667085",
          xmuted: "#98A2B3",
          soft: "#475467",
        },
        border: {
          DEFAULT: "rgba(15,23,42,0.08)",
          strong: "rgba(15,23,42,0.14)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        display: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Cascadia Code", "Consolas", "monospace"],
      },
      borderRadius: {
        sm: "10px",
        DEFAULT: "14px",
        md: "14px",
        lg: "20px",
        xl: "28px",
        "2xl": "34px",
      },
      boxShadow: {
        xs: "0 1px 2px rgba(16,24,40,0.04)",
        sm: "0 2px 8px rgba(16,24,40,0.05)",
        DEFAULT: "0 10px 24px rgba(16,24,40,0.06)",
        md: "0 16px 40px rgba(16,24,40,0.08)",
        lg: "0 24px 64px rgba(16,24,40,0.12)",
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        "fade-in": "fade-in 220ms ease-out",
        "slide-up": "slide-up 280ms cubic-bezier(.22,1,.36,1)",
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
