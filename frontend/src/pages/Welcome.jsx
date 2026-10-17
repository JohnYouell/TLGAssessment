import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ScriptureBanner } from "@/components/ScriptureBanner";

const GOLD_BOX = { box: "bg-gold", num: "text-white", text: "text-black" };
const WHITE_BOX = { box: "bg-white", num: "text-gold", text: "text-black" };
const STEPS = [
  { k: "01", t: "Create your account", d: "Your progress is saved to your profile, rep by rep.", s: GOLD_BOX },
  { k: "02", t: "Read the book", d: "Grab a copy of the book here.", s: WHITE_BOX },
  { k: "03", t: "Complete 7 reps", d: "Seven sequential assessments that follow the book.", s: GOLD_BOX },
  { k: "04", t: "See your growth", d: "Compare the Initial assessment vs all five sections.", s: WHITE_BOX },
];

export default function Welcome({ firstVisit = false }) {
  const { user } = useAuth();
  const name = user?.name?.split(" ")[0];
  return (
    <div data-testid="welcome-page">
      <section className="relative overflow-hidden bg-black bg-cover bg-no-repeat bg-center bg-[image:var(--hero-sm)] max-md:bg-[length:100%_auto] max-md:bg-[position:center_95px] md:bg-left md:bg-[image:var(--hero-lg)] lg:bg-right" style={{ "--hero-sm": "url(/hero-sm-v2.jpg)", "--hero-lg": "url(/hero-bg-v2.jpg)" }} data-testid="welcome-hero">
        <div aria-hidden="true" className="absolute inset-0 bg-black/30 lg:hidden" />
        <div className="relative z-10 mx-auto flex max-w-7xl items-center justify-between gap-12 px-5 py-24 sm:px-8 lg:py-36">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="max-w-2xl">
            <p className="eyebrow" data-testid="welcome-eyebrow">{firstVisit && name ? `Welcome to the gym, ${name}` : "The Lord's Gym · Assessment Series"}</p>
            <h1 className="mt-5 font-heading text-4xl font-bold uppercase leading-[0.95] text-white sm:text-5xl lg:text-6xl" data-testid="welcome-title">
              Become Like Christ.<br /><span className="text-gold">One rep at a time.</span>
            </h1>
            <p className="mt-6 max-w-lg text-base text-zinc-300 max-md:max-w-[230px] md:text-lg">
              A 7-part assessment journey<br className="md:hidden" /> accompanying <em>The Lord's Gym: Discipleship Training, One Rep at a Time.</em> Measure where you stand, put in the work, and see how far you've come.
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
      <ScriptureBanner />
      <section className="mx-auto grid max-w-7xl gap-px bg-line px-0 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((s) => (
          <div key={s.k} className={`${s.s.box} px-8 py-12`} data-testid={`welcome-step-${s.k}`}>
            <span className={`font-heading text-7xl font-bold leading-none lg:text-8xl ${s.s.num}`}>{s.k}</span>
            <h3 className={`mt-4 font-heading text-xl uppercase tracking-wide ${s.s.text}`}>{s.t}</h3>
            <p className={`mt-2 text-sm ${s.s.text}`}>{s.d}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
