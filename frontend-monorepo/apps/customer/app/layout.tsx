import "./globals.css";
import type { Metadata } from "next";
import { Inter, Fraunces, IBM_Plex_Mono } from "next/font/google";
import Providers from "./providers";
import { CustomerSidebar } from "@/components/layout/CustomerSidebar";
import { FloatingTestBubble } from "@/components/layout/FloatingTestBubble";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-ibm-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Customer Dashboard | Voice AI",
  description: "Business owner portal for managing Voice AI agents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${fraunces.variable} ${ibmPlexMono.variable} h-full antialiased`}
    >
      <body className="bg-paper text-ink min-h-full flex flex-col md:flex-row font-sans">
        <Providers>
          <CustomerSidebar />
          <div className="flex-1 flex flex-col min-w-0">
            {children}
          </div>
          <FloatingTestBubble />
        </Providers>
      </body>
    </html>
  );
}
