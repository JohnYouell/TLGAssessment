import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Lock, Trophy, ArrowRight, PlayCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { usePaywall } from "@/context/PaywallContext";
import { AssessmentCard } from "@/components/AssessmentCard";
import { Loader } from "@/components/Loader";

const Tile = ({ icon: Icon, title, text, to, cta, locked, onLocked, testId }) => (
  <div data-testid={testId} className="flex flex-col justify-between border border-line bg-surface p-6 transition-colors duration-150 hover:border-gold">
    <div className="flex items-center justify-between">
      <Icon className="h-6 w-6 text-gold" />
      {locked && <Lock className="h-6 w-6 text-gold" data-testid={`${testId}-padlock`} />}
    </div>
    <div className="mt-6">
      <h3 className="font-heading text-2xl uppercase text-white">{title}</h3>
      <p className="mt-2 text-sm text-zinc-400">{text}</p>
    </div>
    {locked ? (
      <button type="button" onClick={onLocked} className="mt-6 inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest text-gold" data-testid={`${testId}-unlock`}><Lock className="h-4 w-4" /> Unlock</button>
    ) : (
      <Link to={to} className="mt-6 inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest text-gold transition-colors duration-150 hover:text-gold-hover" data-testid={`${testId}-link`}>{cta} <ArrowRight className="h-4 w-4" /></Link>
    )}
  </div>
);

const ADMIN_LINKS = [["/admin/verses", "Scripture Banner", "admin-verses-link"], ["/admin/pages/about", "About Page", "admin-about-link"], ["/admin/pages/contact", "Contact Page", "admin-contact-link"], ["/admin/codes", "Discount Codes", "admin-codes-link"], ["/admin/videos", "Videos", "admin-videos-link"]];

const AdminTools = () => (
  <div className="mt-16 border-t border-line pt-8" data-testid="admin-tools">
    <p className="eyebrow">Admin Tools</p>
    <div className="mt-3 flex flex-wrap gap-x-10 gap-y-3">
      {ADMIN_LINKS.map(([to, label, tid]) => (
        <Link key={to} to={to} className="text-link inline-flex items-center gap-2 font-heading text-sm uppercase tracking-widest" data-testid={tid}>Edit {label} <ArrowRight className="h-4 w-4" /></Link>
      ))}
    </div>
  </div>
);

export default function Dashboard() {
  const { user } = useAuth();
  const { openPaywall } = usePaywall();
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/assessments").then((r) => setData(r.data));
  }, [user.has_access]);

  if (!data) return <Loader />;
  const items = data.assessments;
  const free = items.filter((a) => a.tier === "free");
  const paid = items.filter((a) => a.tier === "paid");
  const done = items.filter((a) => a.status === "completed").length;
  const locked = !data.has_access;

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:py-20" data-testid="dashboard-page">
      <div className="flex flex-col gap-8 border-b border-line pb-10 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="eyebrow">Training Dashboard</p>
          <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl lg:text-6xl" data-testid="dashboard-greeting">Keep lifting, {user.name.split(" ")[0]}.</h1>
        </div>
        <div className="flex items-end gap-4" data-testid="dashboard-reps-counter">
          <span className="font-heading text-7xl font-bold leading-none text-gold">{done}</span>
          <span className="pb-2 font-heading text-xl uppercase tracking-widest text-zinc-400">/ {items.length} reps<br />complete</span>
        </div>
      </div>

      <section className="mt-12" data-testid="tier-free">
        <p className="eyebrow">Actively Training · Free</p>
        <h2 className="mt-2 font-accent text-2xl font-bold text-white">Initial Assessment & Chapter Reviews</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {free.map((a, i) => <AssessmentCard key={a.id} a={a} index={i} />)}
        </div>
      </section>

      <section className="mt-16" data-testid="tier-paid">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">All-Access {locked && "· Locked"}</p>
            <h2 className="mt-2 font-accent text-2xl font-bold text-white">Section Reviews, Final Assessment & Videos</h2>
          </div>
          {locked && <button type="button" onClick={openPaywall} className="btn-gold" data-testid="dashboard-unlock-button"><Lock className="h-4 w-4" /> Unlock Full Access · $40</button>}
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {paid.map((a, i) => <AssessmentCard key={a.id} a={a} index={i} />)}
          <Tile icon={PlayCircle} title="Training Videos" text="Every chapter wrap-up video in one place." to="/videos" cta="Watch" locked={locked} onLocked={openPaywall} testId="videos-tile" />
          <Tile icon={Trophy} title="Master Results" text={data.master_unlocked ? "Your full growth profile is ready." : "Unlocks when you finish the Final Assessment."} to="/master-results" cta={data.master_unlocked ? "View" : "Preview"} locked={locked} onLocked={openPaywall} testId="master-results-tile" />
        </div>
      </section>
      {user.is_admin && <AdminTools />}
    </div>
  );
}
