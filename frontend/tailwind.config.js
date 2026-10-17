import { createRequire } from "node:module";

// Renklerin tek kaynağı src/lib/palette.json; bileşenlerde hex yazılmaz.
const palette = createRequire(import.meta.url)("./src/lib/palette.json");

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: palette,
    },
  },
  plugins: [],
};
