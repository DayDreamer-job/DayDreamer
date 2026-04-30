import { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Us - DayDreamer",
  description:
    "Learn about DayDreamer, your daily destination for fresh job opportunities in India.",
};

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-cream to-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-4xl font-display font-bold text-ink mb-8">
          About <span className="text-brand-500">DayDreamer</span>
        </h1>

        <div className="prose prose-lg max-w-none text-ink/80">
          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Welcome to DayDreamer
            </h2>
            <p className="text-lg leading-relaxed mb-6">
              DayDreamer is your number-one source for fresh job opportunities
              across India. We're dedicated to connecting talented professionals
              and freshers with their dream careers, with a focus on speed,
              accuracy, and genuine opportunities.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Our Mission
            </h2>
            <p className="text-lg leading-relaxed mb-6">
              Founded to revolutionize job hunting in India, DayDreamer has
              grown into a trusted platform for job seekers at all levels. Our
              mission is to simplify the job search process and deliver
              curated, authentic opportunities directly to you every single
              day. We believe in empowering both freshers embarking on their
              career journeys and professionals seeking new challenges.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              What We Offer
            </h2>
            <div className="bg-brand-50 rounded-lg p-6 mb-6">
              <ul className="space-y-4">
                <li className="flex gap-3">
                  <span className="text-brand-500 font-bold">✓</span>
                  <span>
                    <strong>Daily Updates:</strong> Fresh job postings added
                    every day across multiple industries
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-brand-500 font-bold">✓</span>
                  <span>
                    <strong>Curated Opportunities:</strong> Verified jobs from
                    legitimate companies, startups, and enterprises
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-brand-500 font-bold">✓</span>
                  <span>
                    <strong>Smart Filtering:</strong> Find jobs by category,
                    experience level, work mode, and job type
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-brand-500 font-bold">✓</span>
                  <span>
                    <strong>Fresher-Friendly:</strong> Dedicated section for
                    internships and entry-level positions
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-brand-500 font-bold">✓</span>
                  <span>
                    <strong>Remote Opportunities:</strong> Work from anywhere
                    with our dedicated remote jobs section
                  </span>
                </li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Industries We Cover
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  title: "Technology",
                  desc: "Software development, IT, DevOps, and tech startups",
                },
                {
                  title: "Design & Creative",
                  desc: "UI/UX, Graphic Design, and content creation roles",
                },
                {
                  title: "Marketing & Sales",
                  desc: "Digital marketing, B2B sales, and business development",
                },
                {
                  title: "Finance & Business",
                  desc: "Accounting, business analysis, and finance operations",
                },
              ].map((industry, idx) => (
                <div
                  key={idx}
                  className="bg-white border-2 border-brand-100 rounded-lg p-4"
                >
                  <h3 className="font-bold text-ink mb-2">{industry.title}</h3>
                  <p className="text-sm text-ink/60">{industry.desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Our Team
            </h2>
            <p className="text-lg leading-relaxed mb-6">
              We are a passionate team of professionals dedicated to creating
              the best job discovery experience. Our commitment to accuracy,
              quality, and user experience drives everything we do. We work
              tirelessly to ensure that every job listed on DayDreamer is
              legitimate and valuable to your career journey.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Why DayDreamer?
            </h2>
            <div className="bg-brand-50 rounded-lg p-6">
              <ul className="space-y-3 text-lg">
                <li>
                  🎯 <strong>Accuracy First:</strong> Every job is verified for
                  legitimacy
                </li>
                <li>
                  ⚡ <strong>Speed:</strong> New opportunities added daily at
                  7 AM IST
                </li>
                <li>
                  🎓 <strong>Inclusive:</strong> Opportunities for freshers,
                  experienced professionals, and everyone in between
                </li>
                <li>
                  🌍 <strong>Pan-India:</strong> Jobs from companies across all
                  major cities
                </li>
                <li>
                  💼 <strong>Professional:</strong> Authentic job descriptions
                  and honest requirements
                </li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Get In Touch
            </h2>
            <p className="text-lg leading-relaxed mb-6">
              We'd love to hear from you! Whether you have feedback, questions,
              or partnership inquiries, feel free to{" "}
              <a
                href="/contact"
                className="text-brand-500 font-semibold hover:text-brand-600"
              >
                contact us
              </a>
              . We're here to help you find your dream job.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
