import type { Metadata } from "next";
import "./globals.css";
import { ConvexClientProvider } from "@/components/ConvexProvider";

export const metadata: Metadata = {
  title: "Mission Control",
  description: "Task board for Ahmed & OpenClaw",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ConvexClientProvider>{children}</ConvexClientProvider>
      </body>
    </html>
  );
}
