import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/animation/Providers";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { PageTransition } from "@/components/animation/PageTransition";
import { siteConfig } from "@/lib/site";

const geist = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),

  title: {
    default: `${siteConfig.name} — AI Engineer`,
    template: `%s — ${siteConfig.name}`,
  },

  description: siteConfig.description,

  keywords: [
    "Touqeer Ali",
    "AI Engineer",
    "RAG Developer",
    "Agentic AI Developer",
    "AI Agent Developer",
    "LangGraph",
    "FastAPI",
    "Next.js",
  ],

  authors: [{ name: siteConfig.name }],
  creator: siteConfig.name,

  // FAVICON
  icons: {
    icon: "/my_image/1706428239229.jpg",
    shortcut: "/my_image/1706428239229.jpg",
    apple: "/my_image/1706428239229.jpg",
  },

  openGraph: {
    type: "website",
    title: `${siteConfig.name} — AI Engineer`,
    description: siteConfig.description,
    url: siteUrl,
    siteName: siteConfig.name,
  },

  twitter: {
    card: "summary_large_image",
    title: `${siteConfig.name} — AI Engineer`,
    description: siteConfig.description,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    {
      media: "(prefers-color-scheme: dark)",
      color: "#080b0d",
    },
    {
      media: "(prefers-color-scheme: light)",
      color: "#f4f5f1",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geist.variable} ${geistMono.variable}`}>
        <Providers>
          <Navbar />

          <main>
            <PageTransition>{children}</PageTransition>
          </main>

          <Footer />
        </Providers>
      </body>
    </html>
  );
}