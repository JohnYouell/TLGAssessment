import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const STEPS = [
  { k: "01", t: "Create your account", d: "Your progress is saved to your profile, rep by rep." },
  { k: "02", t: "Complete 7 reps", d: "Seven sequential assessments that follow the book." },
  { k: "03", t: "See your growth", d: "Compare Day 1 to Today across all five sections." },
];

export default function Welcome({ firstVisit = false }) {
  const { user } = useAuth();
  const name = user?.name?.split(" ")[0];
  return (
    <div data-testid="welcome-page">
      <section className="relative overflow-hidden">
        <img src="/gateway.jpg" alt="" className="absolute inset-0 h-full w-full object-cover object-center opacity-40" />
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-black/20" />
        <div className="relative mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-36">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="max-w-2xl">
            <p className="eyebrow" data-testid="welcome-eyebrow">{firstVisit && name ? `Welcome to the gym, ${name}` : "The Lord's Gym · Assessment Series"}</p>
            <h1 className="mt-5 font-heading text-4xl font-bold uppercase leading-[0.95] text-white sm:text-5xl lg:text-6xl" data-testid="welcome-title">
              Train your soul.<br /><span className="text-gold">One rep at a time.</span>
            </h1>
            <p className="mt-6 max-w-lg text-base text-zinc-300 md:text-lg">
              A 7-part assessment journey accompanying <em>The Lord's Gym: Discipleship Training, One Rep at a Time.</em> Measure where you stand, put in the work, and see how far you've come.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-6">
              <Link to={user ? "/dashboard" : "/register"} className="btn-gold" data-testid="welcome-primary-cta">
                {user ? (firstVisit ? "Begin Rep 1" : "Enter the Gym") : "Begin Your Training"} <ArrowRight className="h-4 w-4" />
              </Link>
              {!user && <Link to="/login" className="text-link" data-testid="welcome-signin-link">I already have an account</Link>}
            </div>
          </motion.div>
        </div>
      </section>
      <section className="mx-auto grid max-w-7xl gap-px bg-line px-0 sm:grid-cols-3">
        {STEPS.map((s) => (
          <div key={s.k} className="bg-ink px-8 py-12" data-testid={`welcome-step-${s.k}`}>
            <span className="font-heading text-5xl font-bold text-gold/80">{s.k}</span>
            <h3 className="mt-4 font-heading text-xl uppercase tracking-wide text-white">{s.t}</h3>
            <p className="mt-2 text-sm text-zinc-400">{s.d}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
