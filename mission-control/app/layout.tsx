import type { Metadata } from "next";
import "./globals.css";
import { CommandPalette } from "@/components/command-palette";
import { StatusBar } from "@/components/status-bar";
import { ThemeProvider } from "@/lib/theme-provider";
import { KeyboardShortcutsModal } from "@/components/keyboard-shortcuts";

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
    <html lang="en" suppressHydrationWarning>
      <body className="bg-[var(--background)] text-[var(--foreground)] antialiased pb-10">
        <ThemeProvider>
          {children}
          <CommandPalette />
          <KeyboardShortcutsModal />
          <StatusBar />
        </ThemeProvider>
      </body>
    </html>
  );
}
