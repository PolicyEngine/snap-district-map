// Tailwind v4 via @tailwindcss/postcss loads the PolicyEngine ui-kit theme
// tokens through the same pipeline as the other PolicyEngine Next.js apps.
const config = {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};

export default config;
