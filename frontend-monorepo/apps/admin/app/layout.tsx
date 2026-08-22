import type { Metadata } from "next";
import "./globals.css";
import AdminSidebar from "@/components/layout/AdminSidebar";
import ImpersonationBanner from "@/components/layout/ImpersonationBanner";

export const metadata: Metadata = {
  title: "Call AI — Command Center",
  description: "Super Admin Command Center",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-white">
        <div className="flex min-h-screen">
          <AdminSidebar />

          <main className="min-w-0 flex-1 bg-zinc-900">
            <ImpersonationBanner/>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}