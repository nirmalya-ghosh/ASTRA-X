import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AstraX AI — Astronomical Image Analysis Platform",
  description:
    "Research-grade asteroid detection & astronomical image analysis. Ingest FITS datasets, detect moving celestial candidates, and generate observation reports.",
  keywords: [
    "astronomy",
    "FITS",
    "asteroid detection",
    "image analysis",
    "astronomical research",
    "moving object detection",
  ],
};

import { Providers } from "./providers";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
      >
        <div className="starfield" />
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
