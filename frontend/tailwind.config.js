// tailwind.config.js (in your project root)
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html", // Essential if you have Tailwind classes in index.html
    "./src/**/*.{vue,js,ts,jsx,tsx}", // <--- THIS IS KEY FOR VUE COMPONENTS
    // Add any other paths where you use Tailwind classes, e.g., if you have
    // components in a different top-level folder like './lib/**/*.{vue,js}'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};