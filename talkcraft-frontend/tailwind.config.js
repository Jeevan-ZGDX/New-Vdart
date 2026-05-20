/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#1e1e1e",
        border: "#333333",
        accent: "#4CAF50",
        danger: "#f44336",
        warning: "#FF9800",
        "text-secondary": "#888888",
      },
    },
  },
  plugins: [],
};
