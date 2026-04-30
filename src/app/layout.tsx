import type { Metadata } from "next";
import { Playfair_Display, DM_Sans, DM_Mono } from "next/font/google";
import "./globals.css";

import Script from 'next/script'

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

// export const metadata: Metadata = {
//   title: {
//     default: "DayDreamer — Fresh Jobs for Freshers & Professionals",
//     template: "%s | DayDreamer",
//   },
//   description:
//     "Discover the best job opportunities in India. Curated daily for freshers and professionals across tech, design, marketing, data, and more.",
//   keywords: [
//     "jobs india",
//     "fresher jobs",
//     "tech jobs",
//     "remote jobs india",
//     "naukri",
//     "job portal",
//   ],
//   openGraph: {
//     type: "website",
//     locale: "en_IN",
//     url: "https://daydreamer.in",
//     siteName: "DayDreamer",
//     title: "DayDreamer — Fresh Jobs Every Day",
//     description:
//       "Curated job opportunities for freshers and professionals in India.",
//   },
//   twitter: {
//     card: "summary_large_image",
//     title: "DayDreamer — Fresh Jobs Every Day",
//     description:
//       "Curated job opportunities for freshers and professionals in India.",
//   },
//   robots: {
//     index: true,
//     follow: true,
//   },
// };

export const metadata: Metadata = {
  title: {
    default: 'DayDreamer — Latest Jobs in India',
    template: '%s | DayDreamer',
  },
  description: 'Find the latest government jobs, private sector jobs, IT jobs, and more in India. Updated daily.',
  keywords: ['jobs in india', 'sarkari naukri', 'DayDreamer', 'latest jobs 2026', 'jobs newsmatrix', 'government jobs', 'IT jobs india'],
  metadataBase: new URL('https://jobs.newsmatrix.in'),
  alternates: {
    canonical: 'https://jobs.newsmatrix.in',
  },
  verification: {
    google: 'qWla1wyFvfCGTyzx8NrLd9yOz5Y7XvWSYNPbI_-isyA', // from Step 2
  },
  openGraph: {
    siteName: 'DayDreamer',
    type: 'website',
    locale: 'en_IN',
  },
}

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
        {/* // Inside your return, just after <body>: */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-JRH7525Z8H"
          strategy="afterInteractive"
        />
        <Script id="ga4" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-JRH7525Z8H');
          `}
        </Script>
        {/* <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXX"
          crossOrigin="anonymous"
          strategy="lazyOnload"
        /> */}
      </body>
    </html>
  );
}





