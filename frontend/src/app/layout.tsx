import "./globals.css";
import { ReactNode } from "react";
import SidePanel from "../components/SidePanel";
import { ThemeProvider } from "next-themes";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <div className="flex h-screen overflow-hidden bg-background text-foreground font-sans">
            <SidePanel />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
