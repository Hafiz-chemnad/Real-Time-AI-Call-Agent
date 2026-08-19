import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    // This tells Tailwind to look for classes inside both apps and the UI package itself
    "../../apps/customer/app/**/*.{js,ts,jsx,tsx,mdx}",
    "../../apps/customer/components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../apps/admin/app/**/*.{js,ts,jsx,tsx,mdx}",
    "../../apps/admin/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#1B2430",
        paper: "#F3EFE7",
        slate: "#5C6B7A",
        confirm: {
          green: "#3E8168",
        },
        alert: {
          coral: "#D96C56",
        },
        line: {
          amber: "#E8A33D",
        },
      },
      fontFamily: {
        heading: ['var(--font-fraunces)'],
        body: ['var(--font-inter)'],
        mono: ['var(--font-ibm-plex-mono)'],
      },
    },
  },
  plugins: [],
};

export default config;