import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, ArrowRight } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

const ctaLabel = (a) => {
  if (a.status === "completed") return "View Result";
  if (a.status === "in_progress") return "Continue Rep";
  return "Start Rep";
};

export const AssessmentCard = ({ a, index }) => {
  const to = a.status === "completed" ? `/assessment/${a.id}/result` : `/assessment/${a.id}`;
  const pct = a.question_count ? Math.round((a.answered_count / a.question_count) * 100) : 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.4 }}
      data-testid={`assessment-card-${a.id}`}
      className={`group relative flex flex-col justify-between border border-line bg-surface p-6 transition-colors duration-150 ${a.unlocked ? "hover:border-gold" : "opacity-50"}`}
    >
      <div className="flex items-start justify-between gap-4">
        <span className="font-heading text-6xl font-bold leading-none text-white/10 group-hover:text-gold/30">{String(a.id).padStart(2, "0")}</span>
        <StatusBadge status={a.status} testId={`assessment-status-${a.id}`} />
      </div>
      <div className="mt-6">
        <p className="eyebrow">Rep {a.id} of 7 · {a.subtitle}</p>
        <h3 className="mt-2 font-heading text-2xl uppercase tracking-wide text-white" data-testid={`assessment-title-${a.id}`}>{a.title}</h3>
        <p className="mt-2 text-sm text-zinc-400">{a.description}</p>
      </div>
      <div className="mt-6 h-1 w-full bg-white/5">
        <div className="h-1 bg-gold transition-[width] duration-500" style={{ width: `${a.status === "completed" ? 100 : pct}%` }} />
      </div>
      <div className="mt-5 flex items-center justify-between">
        <span className="text-xs text-zinc-500" data-testid={`assessment-score-${a.id}`}>
          {a.status === "completed" ? `${a.score}/${a.max_score} · ${a.designation}` : `${a.answered_count}/${a.question_count} answered`}
        </span>
        {a.unlocked ? (
          <Link to={to} data-testid={`assessment-cta-${a.id}`} className="inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest text-gold transition-colors duration-150 hover:text-gold-hover">
            {ctaLabel(a)} <ArrowRight className="h-4 w-4" />
          </Link>
        ) : (
          <span className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-zinc-500" data-testid={`assessment-locked-${a.id}`}>
            <Lock className="h-4 w-4" /> Locked
          </span>
        )}
      </div>
    </motion.div>
  );
};
