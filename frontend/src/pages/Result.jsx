import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";
import { api, formatApiError } from "@/lib/api";
import { Loader } from "@/components/Loader";

const SectionBreakdown = ({ sections }) => (
  <div className="mt-12" data-testid="result-sections">
    <p className="eyebrow">Section Scores</p>
    <div className="mt-4 grid gap-px bg-line">
      {sections.map((s) => (
        <div key={s.id} className="grid gap-3 bg-surface p-6 md:grid-cols-12 md:items-center" data-testid={`result-section-${s.id}`}>
          <div className="md:col-span-4">
            <p className="text-xs uppercase tracking-widest text-zinc-500">Section {s.id} · {s.chapters}</p>
            <p className="mt-1 font-heading text-lg uppercase text-white">{s.title}</p>
          </div>
          <p className="font-heading text-3xl font-bold text-gold md:col-span-2" data-testid={`result-section-${s.id}-score`}>
            {s.score}<span className="text-base text-zinc-500"> / {s.max}</span>
          </p>
          <div className="md:col-span-6">
            <p className="font-heading uppercase tracking-wide text-white" data-testid={`result-section-${s.id}-designation`}>{s.designation}</p>
            <p className="mt-1 text-sm text-zinc-400">{s.meaning}</p>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default function Result() {
  const { id } = useParams();
  const [res, setRes] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/assessments/${id}/result`).then((r) => setRes(r.data)).catch((e) => setError(formatApiError(e)));
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-5 py-20 text-center" data-testid="result-error">
        <p className="text-zinc-300">{error}</p>
        <Link to="/dashboard" className="text-link mt-6 inline-block" data-testid="result-error-back-link">Back to Dashboard</Link>
      </div>
    );
  }
  if (!res) return <Loader />;
  const pct = Math.round((res.score / res.max_score) * 100);

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8 lg:py-20" data-testid="result-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="result-back-link">
        <ArrowLeft className="h-4 w-4" /> Dashboard
      </Link>
      <p className="eyebrow mt-8">Rep {res.assessment_id} Result · {res.subtitle}</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl" data-testid="result-title">{res.title}</h1>

      <div className="mt-12 grid gap-px bg-line md:grid-cols-12">
        <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="bg-surface p-8 md:col-span-5">
          <p className="eyebrow">{res.sections.length ? "Total Score" : "Your Score"}</p>
          <p className="mt-4 font-heading font-bold leading-none text-white" data-testid="result-score">
            <span className="text-8xl text-gold">{res.score}</span>
            <span className="text-3xl text-zinc-500"> / {res.max_score}</span>
          </p>
          <div className="mt-6 h-1.5 bg-white/10"><div className="h-1.5 bg-gold" style={{ width: `${pct}%` }} /></div>
          <p className="mt-2 text-xs text-zinc-500">{pct}% of maximum</p>
        </motion.div>
        <div className="bg-surface p-8 md:col-span-7">
          <p className="eyebrow">{res.sections.length ? "Overall Designation" : "Designation"}</p>
          <p className="mt-4 font-heading text-4xl font-bold uppercase text-white sm:text-5xl" data-testid="result-designation">{res.designation}</p>
          <p className="mt-6 text-base leading-relaxed text-zinc-300 md:text-lg" data-testid="result-meaning">{res.meaning}</p>
        </div>
      </div>

      {res.sections.length > 0 && <SectionBreakdown sections={res.sections} />}

      <div className="mt-12">
        {res.kind !== "final" ? (
          <Link to="/dashboard" className="btn-gold" data-testid="result-next-button">
            Continue Training <ArrowRight className="h-4 w-4" />
          </Link>
        ) : (
          <Link to="/master-results" className="btn-gold" data-testid="result-master-button">
            View Master Results <ArrowRight className="h-4 w-4" />
          </Link>
        )}
      </div>
    </div>
  );
}
