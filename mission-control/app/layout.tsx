import type { Metadata } from "next";
import "./globals.css";
import { CommandPalette } from "@/components/command-palette";

export const metadata: Metadata = {
  title: "Mission Control v3",
  description: "Next.js and Tailwind control center with auth, calendar, CRM, and settings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-[#080C16] text-[#e2e8f0] antialiased">
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
