import type { Metadata } from "next";

import { Providers } from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "Opposing Counsel Simulator",
  description: "Clause-level contract negotiation engine for legal review workflows.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
