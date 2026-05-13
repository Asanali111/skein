import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#fbf8f4",
        fg: "#1c1c1a",
        muted: "#6a665c",
        brand: "#d97757",
        divider: "#e8e3d8",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "ui-serif", "Georgia", "serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      maxWidth: {
        content: "920px",
      },
      fontSize: {
        hero: ["6rem", { lineHeight: "1.02", letterSpacing: "-0.04em" }],
      },
    },
  },
  plugins: [],
};

export default config;
