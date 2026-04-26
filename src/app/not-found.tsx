import Link from 'next/link'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'

export default function NotFound() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen flex flex-col items-center justify-center text-center px-4">
        <div className="font-display text-[120px] font-bold text-cream-border leading-none select-none">404</div>
        <h1 className="font-display text-3xl font-bold text-ink -mt-4 mb-3">Page Not Found</h1>
        <p className="text-ink-subtle max-w-md mb-8">
          The job or page you're looking for doesn't exist or may have been removed.
        </p>
        <div className="flex gap-3">
          <Link href="/jobs" className="btn-primary">Browse All Jobs</Link>
          <Link href="/" className="btn-secondary">Go Home</Link>
        </div>
      </main>
      <Footer />
    </>
  )
}
