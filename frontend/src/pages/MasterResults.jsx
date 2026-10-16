import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUp, ArrowDown, Minus, Lock, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { Loader } from "@/components/Loader";

const Change = ({ v, testId }) => {
  if (v > 0) return <span data-testid={testId} className="inline-flex items-center gap-1 font-semibold text-green-500"><ArrowUp className="h-4 w-4" />+{v}</span>;
  if (v < 0) return <span data-testid={testId} className="inline-flex items-center gap-1 text-red-400"><ArrowDown className="h-4 w-4" />{v}</span>;
  return <span data-testid={testId} className="inline-flex items-center gap-1 text-zinc-500"><Minus className="h-4 w-4" />0</span>;
};

const Locked = () => (
  <div className="relative mt-12 border border-line" data-testid="master-locked">
    <div className="pointer-events-none select-none p-8 opacity-30 blur-sm">
      {[...Array(6)].map((_, i) => <div key={i} className="mb-4 h-8 bg-white/10" />)}
    </div>
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/60 px-6 text-center">
      <Lock className="h-10 w-10 text-gold" />
      <p className="mt-4 font-heading text-2xl uppercase text-white">Complete all 7 reps to unlock Master Results</p>
      <Link to="/dashboard" className="btn-gold mt-8" data-testid="master-locked-dashboard-button">Back to Training</Link>
    </div>
  </div>
);

export default function MasterResults() {
  const [data, setData] = useState(null);
  const [locked, setLocked] = useState(false);

  useEffect(() => {
    api.get("/master-results").then((r) => setData(r.data)).catch(() => setLocked(true));
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 lg:py-20" data-testid="master-results-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="master-back-link">
        <ArrowLeft className="h-4 w-4" /> Dashboard
      </Link>
      <p className="eyebrow mt-8">Final Scorecard</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl lg:text-6xl">Master Results</h1>
      <p className="mt-4 max-w-2xl text-zinc-400">Your Day 1 baseline compared to Today, across all five sections of the book.</p>
      {locked ? <Locked /> : !data ? <Loader /> : <MasterTable data={data} />}
    </div>
  );
}

const MasterTable = ({ data }) => (
  <div className="mt-12 overflow-x-auto border border-line" data-testid="master-table-wrapper">
    <table className="w-full min-w-[560px] text-left" data-testid="master-table">
      <thead className="bg-surface-2">
        <tr className="font-heading text-xs uppercase tracking-[0.18em] text-gold">
          {["Sections", "Chapters", "Day 1 Score", "Today Score", "Change"].map((h) => <th key={h} className="px-3 py-4 sm:px-4">{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.rows.map((r, i) => (
          <tr key={r.section} className="border-t border-line bg-surface text-sm text-zinc-200" data-testid={`master-row-${i + 1}`}>
            <td className="px-4 py-3 font-semibold text-white">{r.section}</td>
            <td className="px-4 py-3 text-zinc-400">{r.chapters}</td>
            <td className="px-4 py-3" data-testid={`master-row-${i + 1}-day1`}>{r.day1}</td>
            <td className="px-4 py-3" data-testid={`master-row-${i + 1}-today`}>{r.today}</td>
            <td className="px-4 py-3"><Change v={r.change} testId={`master-row-${i + 1}-change`} /></td>
          </tr>
        ))}
        <tr className="border-t-2 border-gold bg-gold/10 font-heading text-base uppercase text-white" data-testid="master-total-row">
          <td className="px-4 py-4 font-bold">Total</td>
          <td className="px-4 py-4 text-zinc-300">Total out of {data.total.max}</td>
          <td className="px-4 py-4" data-testid="master-total-day1">{data.total.day1}</td>
          <td className="px-4 py-4" data-testid="master-total-today">{data.total.today}</td>
          <td className="px-4 py-4"><Change v={data.total.change} testId="master-total-change" /></td>
        </tr>
      </tbody>
    </table>
  </div>
);
