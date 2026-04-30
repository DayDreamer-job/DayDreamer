import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy - DayDreamer",
  description: "Privacy policy for DayDreamer job portal.",
};

export default function Privacy() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-cream to-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-4xl font-display font-bold text-ink mb-2">
          Privacy <span className="text-brand-500">Policy</span>
        </h1>
        <p className="text-ink/60 mb-8">Last updated: April 2026</p>

        <div className="prose prose-lg max-w-none text-ink/80">
          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Overview
            </h2>
            <p className="text-lg leading-relaxed">
              At DayDreamer, accessible at jobs.newsmatrix.in, your privacy is our
              top priority. This Privacy Policy explains what information we
              collect, how we use it, and your rights regarding your data. By
              using our website, you consent to our privacy practices outlined
              below.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Information We Collect
            </h2>
            <p className="text-lg leading-relaxed mb-4">
              We collect information in the following ways:
            </p>
            <ul className="list-disc pl-6 space-y-3 text-lg">
              <li>
                <strong>Account Information:</strong> When you register, we
                collect your name, email address, phone number, and resume
              </li>
              <li>
                <strong>Communication Data:</strong> Messages, emails, and
                inquiries you send us
              </li>
              <li>
                <strong>Usage Data:</strong> Pages visited, time spent, clicks,
                and search queries
              </li>
              <li>
                <strong>Device Information:</strong> Browser type, IP address,
                operating system, and device type
              </li>
              <li>
                <strong>Cookies:</strong> We use cookies to enhance user
                experience
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              How We Use Your Information
            </h2>
            <p className="text-lg leading-relaxed mb-4">
              We use your information to:
            </p>
            <ul className="list-disc pl-6 space-y-3 text-lg">
              <li>Provide, operate, and maintain our website and services</li>
              <li>
                Send you personalized job recommendations based on your profile
              </li>
              <li>
                Communicate with you about updates, new features, and support
              </li>
              <li>
                Improve user experience and website performance through analytics
              </li>
              <li>Prevent fraud and ensure platform security</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Cookies and Web Beacons
            </h2>
            <p className="text-lg leading-relaxed">
              DayDreamer uses cookies to store your preferences, login
              information, and browsing behavior. These help us remember you and
              optimize your experience. You can disable cookies through your
              browser settings, though some features may not work properly.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Third-Party Services
            </h2>
            <p className="text-lg leading-relaxed">
              DayDreamer may use third-party services (Google Analytics, payment
              processors) that have their own privacy policies. We are not
              responsible for their practices. We recommend reviewing their
              policies before using our platform.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Data Security
            </h2>
            <p className="text-lg leading-relaxed">
              We implement industry-standard security measures to protect your
              personal information. However, no method of transmission over the
              internet is completely secure. While we strive to protect your
              data, we cannot guarantee absolute security.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Your Rights
            </h2>
            <p className="text-lg leading-relaxed mb-4">
              You have the following rights regarding your data:
            </p>
            <ul className="list-disc pl-6 space-y-3 text-lg">
              <li>
                <strong>Right to Access:</strong> Request a copy of your
                personal data
              </li>
              <li>
                <strong>Right to Rectification:</strong> Correct inaccurate
                information
              </li>
              <li>
                <strong>Right to Erasure:</strong> Request deletion of your data
                (with exceptions)
              </li>
              <li>
                <strong>Right to Restrict:</strong> Limit how we use your data
              </li>
              <li>
                <strong>Right to Data Portability:</strong> Receive your data in
                a portable format
              </li>
            </ul>
            <p className="text-lg leading-relaxed mt-4">
              To exercise any of these rights, contact us at
              jobs@daydreamer.in
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Children's Privacy
            </h2>
            <p className="text-lg leading-relaxed">
              DayDreamer is not intended for children under 13. We do not
              knowingly collect personal information from children under 13. If
              you believe we have collected such information, please contact us
              immediately at jobs@daydreamer.in.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              GDPR Compliance (For EU Users)
            </h2>
            <p className="text-lg leading-relaxed">
              If you're in the EU, GDPR provides you with additional rights. We
              process your data only with your consent or for legitimate business
              purposes. You can withdraw consent at any time by contacting us.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Policy Updates
            </h2>
            <p className="text-lg leading-relaxed">
              We may update this Privacy Policy periodically. Changes will be
              posted on this page with an updated date. We encourage you to
              review this policy regularly to stay informed about how we protect
              your information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-display font-bold text-ink mb-4">
              Contact Us
            </h2>
            <p className="text-lg leading-relaxed">
              If you have questions about this Privacy Policy or our privacy
              practices, please contact us at:
            </p>
            <div className="bg-brand-50 rounded-lg p-6 mt-4">
              <p>
                <strong>Email:</strong>{" "}
                <a
                  href="mailto:jobs.newsmatrix@gmail.com"
                  className="text-brand-500 hover:text-brand-600"
                >
                  jobs.newsmatrix@gmail.com
                </a>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
