import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthSessionProvider } from "@/components/auth-session-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://chat.vercel.ai"),
  title: "Next.js Chatbot Template",
  description: "Next.js chatbot template using the AI SDK.",
};

export const viewport = {
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "hsl(0 0% 100%)" },
    { media: "(prefers-color-scheme: dark)", color: "hsl(240deg 10% 3.92%)" },
  ],
};

const geist = Geist({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-mono",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      className={`${geist.variable} ${geistMono.variable}`}
      lang="en"
      suppressHydrationWarning
    >
      <head />
      <body className="antialiased">
        <AuthSessionProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            disableTransitionOnChange
            enableSystem
          >
            <TooltipProvider>
              {children}
              <Toaster position="top-center" richColors closeButton />
            </TooltipProvider>
          </ThemeProvider>
        </AuthSessionProvider>
      </body>
    </html>
  );
}
