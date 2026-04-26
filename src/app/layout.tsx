import type { Metadata } from "next";
import { Playfair_Display, DM_Sans, DM_Mono } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "DayDreamer — Fresh Jobs for Freshers & Professionals",
    template: "%s | DayDreamer",
  },
  description:
    "Discover the best job opportunities in India. Curated daily for freshers and professionals across tech, design, marketing, data, and more.",
  keywords: [
    "jobs india",
    "fresher jobs",
    "tech jobs",
    "remote jobs india",
    "naukri",
    "job portal",
  ],
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://daydreamer.in",
    siteName: "DayDreamer",
    title: "DayDreamer — Fresh Jobs Every Day",
    description:
      "Curated job opportunities for freshers and professionals in India.",
  },
  twitter: {
    card: "summary_large_image",
    title: "DayDreamer — Fresh Jobs Every Day",
    description:
      "Curated job opportunities for freshers and professionals in India.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${playfair.variable} ${dmSans.variable} ${dmMono.variable}`}
    >
      <body className="font-body bg-cream text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
