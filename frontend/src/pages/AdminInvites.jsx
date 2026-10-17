import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";

const COLS = [["name", "Reader"], ["spread", "Spread the Word"], ["train", "Train Someone Next"], ["shares", "Total Shares"], ["joined", "Joined"]];

export default function AdminInvites() {
  const { user } = useAuth();
  const [rows, setRows] = useState(null);

  useEffect(() => {
    api.get("/admin/invites").then((r) => setRows(r.data.rows));
  }, []);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!rows) return <Loader />;
  const totals = rows.reduce((t, r) => ({ shares: t.shares + r.shares, joined: t.joined + r.joined }), { shares: 0, joined: 0 });

  return (
    <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-invites-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="admin-invites-back-link"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Invites</h1>
      <p className="mt-3 text-zinc-400" data-testid="admin-invites-totals">{totals.shares} shares · {totals.joined} friends joined</p>
      {rows.length === 0 ? (
        <p className="mt-10 border border-line bg-surface p-8 text-zinc-400" data-testid="admin-invites-empty">No invites yet. Shares from Spread the Word and Train Someone Next will appear here.</p>
      ) : (
        <div className="mt-10 overflow-x-auto border border-line">
          <table className="w-full text-left" data-testid="admin-invites-table">
            <thead className="bg-surface-2">
              <tr className="font-heading text-xs uppercase tracking-[0.18em] text-gold">
                {COLS.map(([k, h]) => <th key={k} className="whitespace-nowrap px-4 py-4">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.email} className="border-t border-line bg-surface text-sm text-zinc-200" data-testid={`admin-invites-row-${i}`}>
                  <td className="px-4 py-3"><p className="font-semibold text-white">{r.name}</p><p className="text-xs text-zinc-500">{r.email}</p></td>
                  <td className="px-4 py-3">{r.spread}</td>
                  <td className="px-4 py-3">{r.train}</td>
                  <td className="px-4 py-3">{r.shares}</td>
                  <td className="px-4 py-3 font-heading text-lg text-gold">{r.joined}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
