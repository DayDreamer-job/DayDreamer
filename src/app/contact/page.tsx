import { Metadata } from "next";
import { Mail, MapPin, Clock } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact Us - DayDreamer",
  description:
    "Get in touch with DayDreamer. We're here to help with any questions or feedback.",
};

export default function Contact() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-cream to-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-4xl font-display font-bold text-ink mb-8">
          Get In <span className="text-brand-500">Touch</span>
        </h1>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Contact Information */}
          <div>
            <h2 className="text-2xl font-display font-bold text-ink mb-8">
              We'd love to hear from you
            </h2>
            <p className="text-lg text-ink/70 mb-8">
              Whether you have questions, feedback, partnership inquiries, or
              just want to say hello, our team is here to help. We typically
              respond to all inquiries within 24 hours.
            </p>

            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <Mail className="w-6 h-6 text-brand-500 mt-1" />
                </div>
                <div>
                  <h3 className="font-bold text-ink mb-1">Email Support</h3>
                  <p className="text-ink/70">
                    <a
                      href="mailto:jobs.newsmatrix@gmail.com"
                      className="text-brand-500 hover:text-brand-600 font-semibold"
                    >
                      jobs.newsmatrix@gmail.com
                    </a>
                  </p>
                  <p className="text-sm text-ink/60 mt-1">
                    Send us your inquiries, feedback, or partnership requests
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <Clock className="w-6 h-6 text-brand-500 mt-1" />
                </div>
                <div>
                  <h3 className="font-bold text-ink mb-1">Response Time</h3>
                  <p className="text-ink/70">
                    We strive to respond to all inquiries within 24 hours during
                    business days.
                  </p>
                  <p className="text-sm text-ink/60 mt-1">
                    Urgent matters are prioritized
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <MapPin className="w-6 h-6 text-brand-500 mt-1" />
                </div>
                <div>
                  <h3 className="font-bold text-ink mb-1">Based In</h3>
                  <p className="text-ink/70">India</p>
                  <p className="text-sm text-ink/60 mt-1">
                    Serving job seekers across India
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div>
            <div className="bg-white rounded-lg border-2 border-brand-100 p-8">
              <h3 className="text-xl font-bold text-ink mb-6">Send us a message</h3>
              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-4 py-2 border border-brand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Your name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-ink mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    className="w-full px-4 py-2 border border-brand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-ink mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-4 py-2 border border-brand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="How can we help?"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-ink mb-2">
                    Message
                  </label>
                  <textarea
                    required
                    rows={4}
                    className="w-full px-4 py-2 border border-brand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Your message here..."
                  ></textarea>
                </div>

                <button
                  type="submit"
                  className="w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Send Message
                </button>
              </form>

              <p className="text-xs text-ink/60 text-center mt-4">
                We respect your privacy and will never share your information.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-16 pt-16 border-t-2 border-brand-100">
          <h2 className="text-2xl font-display font-bold text-ink mb-8">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            <div className="bg-brand-50 rounded-lg p-6">
              <h3 className="font-bold text-ink mb-2">
                How often are new jobs posted?
              </h3>
              <p className="text-ink/70">
                We update our job listings daily at 7 AM IST. You'll find fresh
                opportunities every morning to kickstart your day!
              </p>
            </div>

            <div className="bg-brand-50 rounded-lg p-6">
              <h3 className="font-bold text-ink mb-2">
                Are all jobs verified?
              </h3>
              <p className="text-ink/70">
                Yes! Every job posted on DayDreamer is verified for legitimacy.
                We work hard to ensure only genuine opportunities are listed.
              </p>
            </div>

            <div className="bg-brand-50 rounded-lg p-6">
              <h3 className="font-bold text-ink mb-2">
                Can I post a job on DayDreamer?
              </h3>
              <p className="text-ink/70">
                We're always looking to partner with reputable companies. Please
                reach out to us at jobs@daydreamer.in with details about your
                organization.
              </p>
            </div>

            <div className="bg-brand-50 rounded-lg p-6">
              <h3 className="font-bold text-ink mb-2">
                Do you have jobs for freshers?
              </h3>
              <p className="text-ink/70">
                Absolutely! We have a dedicated section for fresher jobs and
                internships. Check our "Fresher Jobs" category to explore
                entry-level opportunities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
