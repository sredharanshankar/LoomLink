import type { Config } from "tailwindcss";
import defaults from "tailwindcss/colors";
import plugin from "tailwindcss/plugin";

type Scale = Record<string, string>;
const SHADES = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"];

const brand: Scale = {
  50: "#eef2ff", 100: "#e0e7ff", 200: "#c7d2fe", 300: "#a5b4fc", 400: "#818cf8",
  500: "#6366f1", 600: "#4f46e5", 700: "#4338ca", 800: "#3730a3", 900: "#312e81", 950: "#1e1b4b",
};

// Neutral ramp for dark mode: low shades become surfaces, high shades become text.
const DARK_GRAY: Scale = {
  50: "#161b24", 100: "#1c222d", 200: "#272e3a", 300: "#363e4c", 400: "#6b7585", 500: "#8b95a6",
  600: "#a9b2c0", 700: "#c5ccd7", 800: "#dde2ea", 900: "#eef1f6", 950: "#f8fafc",
};
const DARK_SLATE: Scale = { ...DARK_GRAY, 50: "#0b0e14" };
const DARK_SURFACE = "#11151d";

const NEUTRALS: Record<string, Scale> = { gray: DARK_GRAY, slate: DARK_SLATE };
const CHROMATIC: Record<string, Scale> = {
  brand,
  red: defaults.red, rose: defaults.rose, orange: defaults.orange, amber: defaults.amber,
  yellow: defaults.yellow, lime: defaults.lime, green: defaults.green, emerald: defaults.emerald,
  teal: defaults.teal, cyan: defaults.cyan, sky: defaults.sky, blue: defaults.blue,
  indigo: defaults.indigo, violet: defaults.violet, purple: defaults.purple, pink: defaults.pink,
};

const rgb = (hex: string) => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const triplet = (c: number[]) => c.map(Math.round).join(" ");
const mix = (a: string, b: string, t: number) => {
  const [x, y] = [rgb(a), rgb(b)];
  return triplet(x.map((v, i) => v * t + y[i] * (1 - t)));
};

// Pale tints become tints over the dark surface, mid tones stay saturated so solid
// buttons keep their identity, and dark text shades flip light.
function darkChromatic(s: Scale): Scale {
  return {
    50: mix(s[500], DARK_SURFACE, 0.1),
    100: mix(s[500], DARK_SURFACE, 0.16),
    200: mix(s[500], DARK_SURFACE, 0.28),
    300: mix(s[500], DARK_SURFACE, 0.5),
    400: triplet(rgb(s[400])),
    500: triplet(rgb(s[500])),
    600: triplet(rgb(s[500])),
    700: triplet(rgb(s[400])),
    800: triplet(rgb(s[300])),
    900: triplet(rgb(s[200])),
    950: triplet(rgb(s[100])),
  };
}

// Fills keep their saturated solid shades in dark mode (white text stays legible on buttons);
// only the pale tints become dark tints.
function darkChromaticFill(s: Scale): Scale {
  const tints = darkChromatic(s);
  return {
    ...Object.fromEntries(SHADES.map((k) => [k, triplet(rgb(s[k]))])),
    50: tints[50], 100: tints[100], 200: tints[200], 300: tints[300],
  };
}

function lightVars() {
  const out: Record<string, string> = { "--surface": "255 255 255" };
  const all = { gray: defaults.gray, slate: defaults.slate, ...CHROMATIC };
  for (const [name, s] of Object.entries(all))
    for (const k of SHADES) out[`--c-${name}-${k}`] = triplet(rgb(s[k]));
  for (const [name, s] of Object.entries(CHROMATIC))
    for (const k of SHADES) out[`--f-${name}-${k}`] = triplet(rgb(s[k]));
  return out;
}

function darkVars() {
  const out: Record<string, string> = { "--surface": triplet(rgb(DARK_SURFACE)) };
  for (const [name, s] of Object.entries(NEUTRALS))
    for (const k of SHADES) out[`--c-${name}-${k}`] = triplet(rgb(s[k]));
  for (const [name, s] of Object.entries(CHROMATIC)) {
    const d = darkChromatic(s);
    const f = darkChromaticFill(s);
    for (const k of SHADES) {
      out[`--c-${name}-${k}`] = d[k];
      out[`--f-${name}-${k}`] = f[k];
    }
  }
  return out;
}

const themed = (name: string, prefix = "c") =>
  Object.fromEntries(SHADES.map((k) => [k, `rgb(var(--${prefix}-${name}-${k}) / <alpha-value>)`]));

export default {
  // Palettes re-tone themselves under `.dark`, so `dark:` variants are deliberately unreachable.
  darkMode: ["class", "[data-dark-variants-disabled]"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ...Object.fromEntries(["gray", "slate", ...Object.keys(CHROMATIC)].map((n) => [n, themed(n)])),
        surface: "rgb(var(--surface) / <alpha-value>)",
      },
      backgroundColor: Object.fromEntries(Object.keys(CHROMATIC).map((n) => [n, themed(n, "f")])),
      fontFamily: {
        sans: ["Inter", "Noto Sans", "system-ui", "sans-serif"],
        indic: ["Noto Sans Devanagari", "Noto Sans Telugu", "Noto Sans Tamil", "system-ui", "sans-serif"],
      },
      spacing: { "18": "4.5rem" },
      borderRadius: { card: "0.875rem" },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.06)",
        lift: "0 8px 20px -6px rgb(16 24 40 / 0.12), 0 2px 4px -2px rgb(16 24 40 / 0.06)",
        pop: "0 24px 48px -12px rgb(16 24 40 / 0.28)",
      },
      keyframes: {
        "fade-up": { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "none" } },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-up": "fade-up 0.35s cubic-bezier(0.2, 0.8, 0.2, 1) both",
        "fade-in": "fade-in 0.2s ease-out both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [
    plugin(({ addBase }) => {
      addBase({
        ":root, .theme-light": lightVars(),
        ".dark": darkVars(),
        ".dark .theme-light, .dark .worker-shell": lightVars(),
      });
    }),
  ],
} satisfies Config;
