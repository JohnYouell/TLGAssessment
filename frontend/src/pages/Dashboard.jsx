import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Lock, Trophy, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { AssessmentCard } from "@/components/AssessmentCard";
import { Loader } from "@/components/Loader";

const MasterTile = ({ unlocked, done }) => (
  <div data-testid="master-results-tile" className={`flex flex-col justify-between border p-6 ${unlocked ? "border-gold bg-gold/10" : "border-dashed border-line bg-surface"}`}>
    <div className="flex items-center gap-3">
      {unlocked ? <Trophy className="h-6 w-6 text-gold" /> : <Lock className="h-6 w-6 text-zinc-500" />}
      <p className="eyebrow">Final</p>
    </div>
    <div className="mt-6">
      <h3 className="font-heading text-2xl uppercase text-white">Master Results</h3>
      <p className="mt-2 text-sm text-zinc-400">
        {unlocked ? "Your Day 1 vs. Today comparison is ready." : `Complete all 7 reps to unlock. ${done}/7 done.`}
      </p>
    </div>
    <Link to="/master-results" data-testid="master-results-link" className="mt-6 inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest text-gold transition-colors duration-150 hover:text-gold-hover">
      {unlocked ? "View Master Results" : "Preview"} <ArrowRight className="h-4 w-4" />
    </Link>
  </div>
);

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/assessments").then((r) => setData(r.data));
  }, []);

  if (!data) return <Loader />;
  const done = data.assessments.filter((a) => a.status === "completed").length;

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:py-20" data-testid="dashboard-page">
      <div className="flex flex-col gap-8 border-b border-line pb-10 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="eyebrow">Training Dashboard</p>
          <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl lg:text-6xl" data-testid="dashboard-greeting">
            Keep lifting, {user.name.split(" ")[0]}.
          </h1>
        </div>
        <div className="flex items-end gap-4" data-testid="dashboard-reps-counter">
          <span className="font-heading text-7xl font-bold leading-none text-gold">{done}</span>
          <span className="pb-2 font-heading text-xl uppercase tracking-widest text-zinc-400">/ 7 reps<br />complete</span>
        </div>
      </div>
      <div className="mt-6 flex gap-1" data-testid="dashboard-rep-bar">
        {data.assessments.map((a) => (
          <div key={a.id} className={`h-2 flex-1 ${a.status === "completed" ? "bg-gold" : a.status === "in_progress" ? "bg-yellow-500/50" : "bg-white/10"}`} />
        ))}
      </div>
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {data.assessments.map((a, i) => <AssessmentCard key={a.id} a={a} index={i} />)}
        <MasterTile unlocked={data.master_unlocked} done={done} />
      </div>
      {user.is_admin && (
        <div className="mt-12 border-t border-line pt-8" data-testid="admin-tools">
          <p className="eyebrow">Admin Tools</p>
          <div className="mt-3 flex flex-wrap gap-x-10 gap-y-3">
            {[["/admin/verses", "Edit Scripture Banner", "admin-verses-link"], ["/admin/pages/about", "Edit About Page", "admin-about-link"], ["/admin/pages/contact", "Edit Contact Page", "admin-contact-link"]].map(([to, label, tid]) => (
              <Link key={to} to={to} className="text-link inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest" data-testid={tid}>
                {label} <ArrowRight className="h-4 w-4" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
