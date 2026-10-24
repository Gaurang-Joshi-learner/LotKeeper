const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

/** Colours are CSS variables (see index.css) so dark mode is a variable swap, not a rewrite. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        floor: token("floor"),
        surface: token("surface"),
        ink: token("ink"),
        muted: token("muted"),
        line: token("line"),
        enamel: token("enamel"),
        plate: token("plate"),
        brake: token("brake"),
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "system-ui", "sans-serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
