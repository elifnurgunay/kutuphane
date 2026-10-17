/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // bileşenlerde hex yazılmaz, yalnızca bu token'lar kullanılır.
      colors: {
        brand: "#6E3511",
        leaf: "#597928",
        sage: "#91AC67",
        cream: "#FCECD8",
        danger: "#A63A2B",
        warning: "#C98A2E",
        surface: "#FFFAF3",
        ink: "#3B2416",
      },
    },
  },
  plugins: [],
};
