import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/*.json$',
          '/api/',
        ],
      },
    ],
    sitemap: 'https://jobs.newsmatrix.in/sitemap.xml',
    host: 'https://jobs.newsmatrix.in',
  }
}