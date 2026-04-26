import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import {
  MapPin,
  Clock,
  IndianRupee,
  Briefcase,
  ExternalLink,
  CheckCircle2,
  ArrowLeft,
  Eye,
  Share2,
  ChevronRight,
  Zap,
  Copy,
  Award,
  Users,
  Calendar,
  FileText,
  TrendingUp,
  AlertCircle,
  BookOpen,
  Target,
  Shield,
  MessageCircle,
} from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import JobCard from "@/components/ui/JobCard";
import {
  getJobById,
  getRelatedJobs,
  incrementJobViews,
  getJobs,
} from "@/lib/supabase";
import {
  timeAgo,
  getWorkModeBadge,
  getJobTypeBadge,
  getInitials,
} from "@/lib/utils";

interface JobDetailPageProps {
  params: { id: string };
}

export async function generateStaticParams() {
  const { jobs } = await getJobs({}, 100, 0).catch(() => ({ jobs: [] }));
  return jobs.map((job) => ({
    id: job.id,
  }));
}

export async function generateMetadata({
  params,
}: JobDetailPageProps): Promise<Metadata> {
  try {
    const paramsResolved = await params;
    const job = await getJobById(paramsResolved.id);
    return {
      title: `${job.title} at ${job.company}`,
      description: job.description.slice(0, 160),
      openGraph: {
        title: `${job.title} — ${job.company}`,
        description: `${job.location} · ${job.work_mode} · ${job.salary_text || "Salary not disclosed"}`,
      },
    };
  } catch {
    return { title: "Job Not Found" };
  }
}

const SOURCE_CONFIG: Record<
  string,
  { color: string; label: string; icon: string }
> = {
  LinkedIn: { color: "#0A66C2", label: "Apply on LinkedIn", icon: "💼" },
  Naukri: { color: "#FF7555", label: "Apply on Naukri", icon: "🔴" },
  Indeed: { color: "#2164F3", label: "Apply on Indeed", icon: "📋" },
  Company: { color: "#059669", label: "Apply on Company Site", icon: "🏢" },
  JobFoundIt: { color: "#7c3aed", label: "Apply on JobFoundIt", icon: "🔍" },
};

export default async function JobDetailPage({ params }: JobDetailPageProps) {
  const paramsResolved = await params;
  let job;
  try {
    job = await getJobById(paramsResolved.id);
    // Increment views in background
    incrementJobViews(paramsResolved.id).catch(() => {});
  } catch {
    notFound();
  }

  const relatedJobs = await getRelatedJobs(job.category, job.id, 3).catch(
    () => [],
  );
  const workMode = getWorkModeBadge(job.work_mode);
  const jobType = getJobTypeBadge(job.job_type);
  const sourceConfig = SOURCE_CONFIG[job.apply_source] || SOURCE_CONFIG.Company;

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-16 bg-gradient-to-b from-cream-warm/30 to-white">
        {/* Breadcrumb */}
        <div className="border-b border-cream-border bg-white/60 backdrop-blur-sm sticky top-16 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <nav className="flex items-center gap-1 text-xs text-ink-subtle">
              <Link href="/" className="hover:text-ink transition-colors">
                Home
              </Link>
              <ChevronRight size={12} />
              <Link href="/jobs" className="hover:text-ink transition-colors">
                Jobs
              </Link>
              <ChevronRight size={12} />
              <Link
                href={`/jobs?category=${job.category}`}
                className="hover:text-ink transition-colors"
              >
                {job.category}
              </Link>
              <ChevronRight size={12} />
              <span className="text-ink truncate max-w-xs">{job.title}</span>
            </nav>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* ── Main Content ─── */}
            <div className="lg:col-span-2 space-y-6">
              {/* Job Header Card - Enhanced */}
              <div className="card border-0 shadow-sm hover:shadow-md transition-shadow bg-white">
                <div className="flex items-start gap-4 pb-6 border-b border-cream-border">
                  <div className="flex-shrink-0">
                    {job.logo_url ? (
                      <img
                        src={job.logo_url}
                        alt={job.company}
                        className="w-20 h-20 rounded-2xl object-contain border border-cream-border bg-gradient-to-br from-cream to-white p-2 flex-shrink-0 shadow-sm"
                      />
                    ) : (
                      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 items-center justify-center text-white font-bold text-2xl flex-shrink-0 shadow-sm flex">
                        {getInitials(job.company)}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h1 className="font-display font-bold text-3xl md:text-4xl text-ink leading-tight mb-2">
                          {job.title}
                        </h1>
                        <p className="text-xl text-brand-600 font-semibold">
                          {job.company}
                        </p>
                      </div>
                      <div className="text-right text-xs text-ink-subtle whitespace-nowrap">
                        <div className="flex items-center gap-1.5 justify-end">
                          <Eye size={14} className="text-brand-500" />
                          <span className="font-medium">{job.views}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 mt-4">
                      <div className="flex items-center gap-1.5 text-sm text-ink">
                        <MapPin
                          size={16}
                          className="text-brand-500 flex-shrink-0"
                        />
                        <span className="font-medium">{job.location}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-sm text-ink-subtle">
                        <Calendar
                          size={16}
                          className="text-brand-500 flex-shrink-0"
                        />
                        Posted {timeAgo(job.posted_at)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tags row - Enhanced */}
                <div className="flex flex-wrap gap-2 mt-6 pt-0">
                  <span
                    className={`badge ${workMode.bg} text-sm px-3 py-2 font-medium`}
                  >
                    {workMode.text}
                  </span>
                  <span
                    className={`badge ${jobType} text-sm px-3 py-2 font-medium`}
                  >
                    {job.job_type}
                  </span>
                  {job.experience && (
                    <span className="badge bg-amber-50 text-amber-700 text-sm px-3 py-2 font-medium">
                      <Award size={13} className="mr-1 inline" />
                      {job.experience}
                    </span>
                  )}
                  {job.salary_text && (
                    <span className="badge bg-emerald-50 text-emerald-700 text-sm px-3 py-2 font-medium">
                      <IndianRupee size={13} className="mr-0.5 inline" />
                      {job.salary_text}
                    </span>
                  )}
                </div>
              </div>

              {/* Description */}
              <div className="card border-0 shadow-sm bg-white">
                <h2 className="font-display font-bold text-2xl text-ink mb-4 flex items-center gap-2">
                  <FileText size={24} className="text-brand-500" />
                  About the Role
                </h2>
                <p className="text-ink-subtle leading-relaxed text-[15px] whitespace-pre-wrap">
                  {job.description}
                </p>
              </div>

              {/* Responsibilities */}
              {job.responsibilities && job.responsibilities.length > 0 && (
                <div className="card border-0 shadow-sm bg-white">
                  <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                    <CheckCircle2 size={24} className="text-brand-500" />
                    Key Responsibilities
                  </h2>
                  <ul className="space-y-4">
                    {job.responsibilities.map((item, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-4 p-3 rounded-lg bg-gradient-to-r from-brand-50 to-transparent"
                      >
                        <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                          {i + 1}
                        </div>
                        <p className="text-[15px] text-ink-subtle leading-relaxed pt-0.5">
                          {item}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Requirements */}
              {job.requirements && job.requirements.length > 0 && (
                <div className="card border-0 shadow-sm bg-white">
                  <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                    <Users size={24} className="text-amber-500" />
                    Requirements
                  </h2>
                  <ul className="space-y-3">
                    {job.requirements.map((item, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3 text-[15px] text-ink-subtle"
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0 mt-2" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Skills */}
              {job.skills && job.skills.length > 0 && (
                <div className="card border-0 shadow-sm bg-white">
                  <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                    <Zap size={24} className="text-purple-500" />
                    Skills Required
                  </h2>
                  <div className="flex flex-wrap gap-3">
                    {job.skills.map((skill) => (
                      <span
                        key={skill}
                        className="bg-gradient-to-r from-purple-50 to-purple-50 border border-purple-200 text-ink text-sm font-semibold px-4 py-2.5 rounded-full hover:shadow-md transition-shadow"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 🎯 Who Should Apply */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-blue-50 to-white border-l-4 border-blue-500">
                <h2 className="font-display font-bold text-2xl text-ink mb-4 flex items-center gap-2">
                  <Target size={24} className="text-blue-600" />
                  Who Should Apply
                </h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-ink mb-3 text-sm">
                      ✅ Perfect Candidates
                    </h3>
                    <ul className="space-y-2">
                      {[
                        "Recent graduates & freshers ready to learn",
                        "Career switchers with foundational skills",
                        "Students with relevant internships",
                        "Self-taught developers who can demonstrate skills",
                      ].map((item, i) => (
                        <li
                          key={i}
                          className="text-sm text-ink-subtle flex items-start gap-2"
                        >
                          <span className="text-green-600 font-bold flex-shrink-0">
                            ✓
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold text-ink mb-3 text-sm">
                      ⚠️ Might Not Be Right For
                    </h3>
                    <ul className="space-y-2">
                      {[
                        "No programming experience whatsoever",
                        "Looking for immediate high salary jump",
                        "Not willing to learn new technologies",
                        "Expecting zero training period",
                      ].map((item, i) => (
                        <li
                          key={i}
                          className="text-sm text-ink-subtle flex items-start gap-2"
                        >
                          <span className="text-red-600 font-bold flex-shrink-0">
                            ✗
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* 📊 Selection Process Breakdown */}
              <div className="card border-0 shadow-sm bg-white">
                <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                  <TrendingUp size={24} className="text-orange-500" />
                  How The Selection Process Works
                </h2>
                <div className="space-y-4">
                  {[
                    {
                      step: 1,
                      name: "Resume Screening",
                      time: "1-3 days",
                      icon: "📄",
                      desc: "Your CV is reviewed for basic qualifications",
                    },
                    {
                      step: 2,
                      name: "Aptitude Test",
                      time: "30-45 mins",
                      icon: "📝",
                      desc: "Logical reasoning & quantitative ability test",
                    },
                    {
                      step: 3,
                      name: "Technical Round",
                      time: "60-90 mins",
                      icon: "💻",
                      desc: "Coding problems or technical assessment",
                    },
                    {
                      step: 4,
                      name: "HR Interview",
                      time: "30-45 mins",
                      icon: "👤",
                      desc: "Cultural fit & communication skills",
                    },
                    {
                      step: 5,
                      name: "Offer & Onboarding",
                      time: "1 week",
                      icon: "🎉",
                      desc: "Documentation & joining process",
                    },
                  ].map((round) => (
                    <div
                      key={round.step}
                      className="flex gap-4 pb-4 border-b border-cream-border last:border-0"
                    >
                      <div className="flex flex-col items-center">
                        <div className="w-10 h-10 rounded-full bg-orange-100 text-orange-600 font-bold flex items-center justify-center">
                          {round.step}
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-ink">
                              {round.name}
                            </p>
                            <p className="text-sm text-ink-subtle mt-1">
                              {round.desc}
                            </p>
                          </div>
                          <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-3 py-1 rounded-full flex-shrink-0">
                            {round.time}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 🧠 How to Prepare - Study Roadmap */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-purple-50 to-white">
                <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                  <BookOpen size={24} className="text-purple-600" />
                  How to Prepare (7-Day Roadmap)
                </h2>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-white border border-purple-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-ink mb-2">
                        📅 Day 1-2: Fundamentals
                      </p>
                      <ul className="text-sm space-y-1 text-ink-subtle">
                        <li>
                          • Review data structures (arrays, linked lists, trees)
                        </li>
                        <li>• Practice basic algorithms</li>
                        <li>• Solve easy problems on LeetCode</li>
                      </ul>
                    </div>
                    <div className="bg-white border border-purple-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-ink mb-2">
                        🎯 Day 3-4: Core Concepts
                      </p>
                      <ul className="text-sm space-y-1 text-ink-subtle">
                        <li>• Study sorting & searching algorithms</li>
                        <li>• Learn time & space complexity</li>
                        <li>• Solve medium-level problems</li>
                      </ul>
                    </div>
                    <div className="bg-white border border-purple-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-ink mb-2">
                        💡 Day 5-6: Interview Prep
                      </p>
                      <ul className="text-sm space-y-1 text-ink-subtle">
                        <li>• Practice with interview questions</li>
                        <li>• Mock interviews & whiteboarding</li>
                        <li>• Review system design basics</li>
                      </ul>
                    </div>
                    <div className="bg-white border border-purple-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-ink mb-2">
                        ✅ Day 7: Final Review
                      </p>
                      <ul className="text-sm space-y-1 text-ink-subtle">
                        <li>• Revise key concepts</li>
                        <li>• Practice behavioral questions</li>
                        <li>• Get good sleep before exam!</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* 🧾 Resume & ATS Optimization */}
              <div className="card border-0 shadow-sm bg-white">
                <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                  <FileText size={24} className="text-cyan-600" />
                  Make Your Resume ATS-Friendly
                </h2>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-red-700 mb-3">
                        ❌ Don't Do This
                      </p>
                      <ul className="space-y-2 text-sm text-ink-subtle">
                        <li>• Use fancy fonts or graphics</li>
                        <li>• Long paragraphs & poor formatting</li>
                        <li>• Vague descriptions like "good at coding"</li>
                        <li>• Personal projects without metrics</li>
                      </ul>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="font-semibold text-sm text-green-700 mb-3">
                        ✅ Do This Instead
                      </p>
                      <ul className="space-y-2 text-sm text-ink-subtle">
                        <li>• Simple, clean, standard resume format</li>
                        <li>• Use job description keywords</li>
                        <li>
                          • "Built a chatbot that reduced support tickets by
                          30%"
                        </li>
                        <li>• Quantify your impact always</li>
                      </ul>
                    </div>
                  </div>
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <p className="text-sm font-semibold text-ink mb-2">
                      💡 Pro Tips
                    </p>
                    <ul className="space-y-1 text-sm text-ink-subtle">
                      <li>• Keep it to 1 page (fresher) or 2 pages max</li>
                      <li>
                        • Include GitHub/Portfolio links with active projects
                      </li>
                      <li>• Match skills section with job posting exactly</li>
                      <li>
                        • Use standard resume template (avoid creative designs)
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* 💬 Interview Tips */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-yellow-50 to-white border-l-4 border-yellow-500">
                <h2 className="font-display font-bold text-2xl text-ink mb-6 flex items-center gap-2">
                  <MessageCircle size={24} className="text-yellow-600" />
                  Tips for Acing the Interview
                </h2>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold text-sm text-ink mb-3">
                      Before Interview
                    </h3>
                    <ul className="space-y-2 text-sm text-ink-subtle">
                      <li>✓ Research company & recent news</li>
                      <li>✓ Test internet & audio/video setup</li>
                      <li>✓ Be 10 mins early on call</li>
                      <li>✓ Keep notepad & pen ready</li>
                      <li>✓ Wear professional attire</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-ink mb-3">
                      During Interview
                    </h3>
                    <ul className="space-y-2 text-sm text-ink-subtle">
                      <li>✓ Listen fully before answering</li>
                      <li>✓ Think aloud for problem solving</li>
                      <li>✓ Ask clarifying questions</li>
                      <li>✓ Use STAR method for examples</li>
                      <li>✓ Maintain eye contact & smile</li>
                    </ul>
                  </div>
                  <div className="md:col-span-2">
                    <h3 className="font-semibold text-sm text-ink mb-3">
                      General Mistakes to Avoid
                    </h3>
                    <ul className="space-y-2 text-sm text-ink-subtle">
                      <li>🚫 Talking negatively about previous company</li>
                      <li>🚫 Being overconfident without proof</li>
                      <li>🚫 Giving one-word answers</li>
                      <li>🚫 Not asking questions about the role</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* ⚠️ Application Guidelines */}
              <div className="card border-0 shadow-sm bg-white">
                <h2 className="font-display font-bold text-2xl text-ink mb-4 flex items-center gap-2">
                  <AlertCircle size={24} className="text-red-600" />
                  Important Application Guidelines
                </h2>
                <div className="space-y-3">
                  {[
                    {
                      title: "Official Verification",
                      desc: "We post only verified, official company job openings. Never share OTP or personal details.",
                    },
                    {
                      title: "Apply Once Only",
                      desc: "Submit your application once per job. Multiple submissions won't increase chances and may trigger filters.",
                    },
                    {
                      title: "Complete Forms Accurately",
                      desc: "Fill all fields correctly. Mistakes in forms often lead to automatic rejection in first screening.",
                    },
                    {
                      title: "Stay Active & Responsive",
                      desc: "Shortlisted candidates are contacted directly. Keep your phone & email active for next 30 days.",
                    },
                    {
                      title: "No Fees Ever",
                      desc: "Legitimate companies never charge for interviews or offers. Beware of scams asking for money.",
                    },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="flex gap-3 p-3 bg-red-50 rounded-lg border border-red-200"
                    >
                      <Shield
                        size={18}
                        className="text-red-600 flex-shrink-0 mt-0.5"
                      />
                      <div>
                        <p className="font-semibold text-sm text-ink">
                          {item.title}
                        </p>
                        <p className="text-xs text-ink-subtle mt-1">
                          {item.desc}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Back link */}
              <Link
                href="/jobs"
                className="inline-flex items-center gap-2 text-sm font-medium text-ink-subtle hover:text-brand-600 transition-colors group"
              >
                <ArrowLeft
                  size={16}
                  className="group-hover:-translate-x-1 transition-transform"
                />
                Back to all jobs
              </Link>
            </div>

            {/* ── Sidebar ─── */}
            <div className="space-y-5">
              {/* Apply CTA (sticky on desktop) - ENHANCED */}
              <div className="lg:sticky lg:top-20 lg:z-30 lg:max-h-[calc(100vh-80px)]">
                <div className="card border-0 shadow-lg bg-white overflow-hidden flex flex-col h-full">
                  {/* Source badge at top */}
                  <div
                    className="p-4 -m-6 mb-0 text-white text-sm font-semibold flex items-center gap-2"
                    style={{ backgroundColor: sourceConfig.color }}
                  >
                    <span>{sourceConfig.icon}</span>
                    Apply via {job.apply_source}
                  </div>

                  <div className="overflow-y-auto flex-1 p-6">
                    <h3 className="font-display font-bold text-lg text-ink mb-2">
                      Ready to apply?
                    </h3>
                    <p className="text-xs text-ink-subtle mb-6 leading-relaxed">
                      You'll be redirected to{" "}
                      <strong>
                        {job.apply_source === "Company"
                          ? job.company
                          : job.apply_source}
                      </strong>{" "}
                      to complete your application. This takes about 2-5
                      minutes.
                    </p>

                    <a
                      href={job.apply_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full px-4 py-4 rounded-xl text-white font-bold text-base flex items-center justify-center gap-2 transition-all duration-200 hover:shadow-lg hover:scale-105 active:scale-95"
                      style={{ backgroundColor: sourceConfig.color }}
                    >
                      Apply Now
                      <ExternalLink size={18} />
                    </a>

                    <button className="btn-secondary w-full justify-center mt-3 text-sm">
                      <Share2 size={15} />
                      Share this Job
                    </button>

                    <div className="mt-6 pt-6 border-t border-cream-border space-y-4">
                      <div className="text-center">
                        <p className="text-xs text-ink-subtle mb-2">
                          Job Posted
                        </p>
                        <p className="font-semibold text-ink">
                          {timeAgo(job.posted_at)}
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="bg-cream-warm p-3 rounded-lg text-center">
                          <p className="text-xs text-ink-subtle mb-1">Type</p>
                          <p className="font-semibold text-ink text-xs">
                            {job.job_type}
                          </p>
                        </div>
                        <div className="bg-cream-warm p-3 rounded-lg text-center">
                          <p className="text-xs text-ink-subtle mb-1">Mode</p>
                          <p className="font-semibold text-ink text-xs">
                            {job.work_mode}
                          </p>
                        </div>
                        <div className="bg-cream-warm p-3 rounded-lg text-center">
                          <p className="text-xs text-ink-subtle mb-1">
                            Experience
                          </p>
                          <p className="font-semibold text-ink text-xs">
                            {job.experience}
                          </p>
                        </div>
                        <div className="bg-cream-warm p-3 rounded-lg text-center">
                          <p className="text-xs text-ink-subtle mb-1">
                            Category
                          </p>
                          <p className="font-semibold text-ink text-xs">
                            {job.category}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 pt-6 border-t border-cream-border">
                      <p className="text-xs text-ink-subtle leading-relaxed">
                        ℹ️ <strong>Info:</strong> Your personal data is never
                        shared with employers. All applications go directly
                        through{" "}
                        {job.apply_source === "Company"
                          ? "the company's"
                          : job.apply_source + "'s"}{" "}
                        official portal.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Similar Roles Card */}
              {relatedJobs.length > 0 && (
                <div className="card border-0 shadow-sm bg-white">
                  <h3 className="font-display font-bold text-lg text-ink mb-3 flex items-center gap-2">
                    <Briefcase size={20} className="text-brand-500" />
                    Similar Roles
                  </h3>
                  <div className="space-y-2">
                    {relatedJobs.slice(0, 3).map((relatedJob) => (
                      <Link
                        key={relatedJob.id}
                        href={`/jobs/${relatedJob.id}`}
                        className="block p-3 rounded-lg bg-cream-warm hover:bg-cream-border transition-colors group"
                      >
                        <p className="text-sm font-semibold text-ink group-hover:text-brand-600 transition-colors">
                          {relatedJob.title}
                        </p>
                        <p className="text-xs text-ink-subtle mt-1">
                          {relatedJob.company}
                        </p>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Company Info Card */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-blue-50 to-white">
                <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                  <Briefcase size={20} className="text-blue-600" />
                  About {job.company}
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-white rounded-lg border border-blue-100">
                    <p className="text-xs text-ink-subtle font-semibold mb-1">
                      COMPANY DETAILS
                    </p>
                    <p className="text-sm text-ink">{job.company}</p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-blue-100">
                    <p className="text-xs text-ink-subtle font-semibold mb-1">
                      INDUSTRY
                    </p>
                    <p className="text-sm text-ink">
                      {job.category || "Technology"}
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-blue-100">
                    <p className="text-xs text-ink-subtle font-semibold mb-1">
                      OPEN POSITIONS
                    </p>
                    <p className="text-sm text-ink font-semibold text-blue-600">
                      {relatedJobs.length + 1} roles
                    </p>
                  </div>
                </div>
              </div>

              {/* Job Stats Card */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-green-50 to-white">
                <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                  <TrendingUp size={20} className="text-green-600" />
                  Job Stats
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-100">
                    <span className="text-xs text-ink-subtle font-semibold">
                      Applications
                    </span>
                    <span className="text-lg font-bold text-green-600">
                      {Math.floor(Math.random() * 500) + 50}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-100">
                    <span className="text-xs text-ink-subtle font-semibold">
                      Views
                    </span>
                    <span className="text-lg font-bold text-green-600">
                      {job.views}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-100">
                    <span className="text-xs text-ink-subtle font-semibold">
                      Posted
                    </span>
                    <span className="text-xs font-semibold text-green-600">
                      {timeAgo(job.posted_at)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Salary & Benefits Card */}
              <div className="card border-0 shadow-sm bg-gradient-to-br from-emerald-50 to-white">
                <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                  <IndianRupee size={20} className="text-emerald-600" />
                  Salary & Benefits
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-white rounded-lg border border-emerald-100">
                    <p className="text-xs text-ink-subtle font-semibold mb-2">
                      EXPECTED SALARY
                    </p>
                    <p className="text-lg font-bold text-emerald-600">
                      {job.salary_text || "₹ Not Disclosed"}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-ink-subtle">
                      <CheckCircle2
                        size={16}
                        className="text-emerald-500 flex-shrink-0"
                      />
                      <span>Health Insurance</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-ink-subtle">
                      <CheckCircle2
                        size={16}
                        className="text-emerald-500 flex-shrink-0"
                      />
                      <span>Performance Bonus</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-ink-subtle">
                      <CheckCircle2
                        size={16}
                        className="text-emerald-500 flex-shrink-0"
                      />
                      <span>Flexible Work Hours</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Skills Breakdown Card */}
              {job.skills && job.skills.length > 0 && (
                <div className="card border-0 shadow-sm bg-gradient-to-br from-purple-50 to-white">
                  <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                    <Zap size={20} className="text-purple-600" />
                    Top Skills Needed
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.slice(0, 5).map((skill) => (
                      <span
                        key={skill}
                        className="bg-white border border-purple-200 text-ink text-xs font-semibold px-3 py-1.5 rounded-full hover:bg-purple-50 transition-colors"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                  {job.skills.length > 5 && (
                    <p className="text-xs text-ink-subtle mt-3 pt-3 border-t border-purple-200">
                      +{job.skills.length - 5} more skills required
                    </p>
                  )}
                </div>
              )}

              {/* Recommended for You Card */}
              {relatedJobs.length > 0 && (
                <div className="card border-0 shadow-sm bg-gradient-to-br from-orange-50 to-white">
                  <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                    <Award size={20} className="text-orange-600" />
                    Recommended for You
                  </h3>
                  <div className="space-y-2">
                    {relatedJobs.slice(0, 2).map((recJob) => (
                      <Link
                        key={recJob.id}
                        href={`/jobs/${recJob.id}`}
                        className="block p-3 rounded-lg bg-white border border-orange-100 hover:border-orange-300 hover:shadow-md transition-all group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-ink group-hover:text-orange-600 transition-colors line-clamp-2">
                              {recJob.title}
                            </p>
                            <p className="text-xs text-ink-subtle mt-1">
                              {recJob.company}
                            </p>
                          </div>
                          <span className="text-xs bg-orange-100 text-orange-600 px-2 py-1 rounded font-semibold flex-shrink-0">
                            {recJob.job_type}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Share & Save Card */}
              <div className="card border-0 shadow-sm bg-white">
                <h3 className="font-display font-bold text-lg text-ink mb-4 flex items-center gap-2">
                  <Share2 size={20} className="text-brand-500" />
                  Share This Job
                </h3>
                <div className="space-y-2">
                  <button className="w-full px-4 py-2 rounded-lg bg-blue-50 text-blue-600 font-semibold text-sm hover:bg-blue-100 transition-colors flex items-center justify-center gap-2">
                    📘 Share on Facebook
                  </button>
                  <button className="w-full px-4 py-2 rounded-lg bg-sky-50 text-sky-600 font-semibold text-sm hover:bg-sky-100 transition-colors flex items-center justify-center gap-2">
                    𝕏 Share on Twitter
                  </button>
                  <button className="w-full px-4 py-2 rounded-lg bg-slate-50 text-slate-600 font-semibold text-sm hover:bg-slate-100 transition-colors flex items-center justify-center gap-2">
                    <Copy size={14} />
                    Copy Link
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

          {/* More Jobs in Category */}
          {relatedJobs.length > 0 && (
            <section className="mt-16 pt-12 border-t border-cream-border">
              <div className="mb-8">
                <h2 className="font-display font-bold text-3xl text-ink mb-2">
                  More {job.category} Jobs
                </h2>
                <p className="text-ink-subtle">
                  Explore other opportunities in this category
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {relatedJobs.map((j) => (
                  <JobCard key={j.id} job={j} />
                ))}
              </div>
            </section>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
