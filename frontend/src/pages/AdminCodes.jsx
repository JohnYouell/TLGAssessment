import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowLeft, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

const CodeRow = ({ c, onSave, onDelete }) => {
  const [pct, setPct] = useState(c.percent_off);
  return (
    <div className="grid items-center gap-3 border border-line bg-surface p-4 sm:grid-cols-12" data-testid={`code-row-${c.id}`}>
      <span className="font-heading text-lg uppercase tracking-wide text-white sm:col-span-4">{c.code}</span>
      <div className="flex items-center gap-2 sm:col-span-3">
        <Input type="number" min={1} max={100} value={pct} onChange={(e) => setPct(e.target.value)} className="field w-24" data-testid={`code-percent-${c.id}`} />
        <span className="text-zinc-400">% off</span>
      </div>
      <label className="flex items-center gap-2 text-sm text-zinc-300 sm:col-span-2">
        <Switch checked={c.active} onCheckedChange={(v) => onSave(c, Number(pct), v)} data-testid={`code-active-${c.id}`} /> {c.active ? "On" : "Off"}
      </label>
      <span className="text-xs text-zinc-500 sm:col-span-1">{c.uses} uses</span>
      <div className="flex gap-2 sm:col-span-2 sm:justify-end">
        <button type="button" onClick={() => onSave(c, Number(pct), c.active)} className="text-link text-sm" data-testid={`code-save-${c.id}`}>Save</button>
        <button type="button" onClick={() => onDelete(c)} aria-label="Delete" className="text-zinc-400 hover:text-red-400" data-testid={`code-delete-${c.id}`}><Trash2 className="h-4 w-4" /></button>
      </div>
    </div>
  );
};

export default function AdminCodes() {
  const { user } = useAuth();
  const [codes, setCodes] = useState(null);
  const [form, setForm] = useState({ code: "", percent_off: 10 });
  const load = () => api.get("/admin/codes").then((r) => setCodes(r.data.codes));

  useEffect(() => {
    if (user.is_admin) load();
  }, [user.is_admin]);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!codes) return <Loader />;

  const run = async (fn, msg) => {
    try {
      await fn();
      toast.success(msg);
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };
  const save = (c, pct, active) => run(() => api.put(`/admin/codes/${c.id}`, { code: c.code, percent_off: pct, active }), `${c.code} saved`);
  const del = (c) => window.confirm(`Delete code ${c.code}?`) && run(() => api.delete(`/admin/codes/${c.id}`), `${c.code} deleted`);
  const create = (e) => {
    e.preventDefault();
    run(() => api.post("/admin/codes", { ...form, percent_off: Number(form.percent_off) }), "Code created").then(() => setForm({ code: "", percent_off: 10 }));
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-codes-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Discount Codes</h1>
      <p className="mt-3 text-zinc-400">Full Access is $40.00. Codes aren&apos;t case-sensitive and spaces are ignored. 100% codes unlock access without checkout.</p>
      <div className="mt-10 space-y-3">{codes.map((c) => <CodeRow key={c.id} c={c} onSave={save} onDelete={del} />)}</div>
      <form onSubmit={create} className="mt-10 flex flex-wrap items-end gap-3 border-t border-line pt-8" data-testid="code-create-form">
        <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="New code name" required minLength={2} maxLength={40} className="field w-60" data-testid="code-new-name" />
        <Input type="number" min={1} max={100} value={form.percent_off} onChange={(e) => setForm({ ...form, percent_off: e.target.value })} className="field w-24" data-testid="code-new-percent" />
        <span className="pb-3 text-zinc-400">% off</span>
        <button type="submit" className="btn-gold" data-testid="code-create-button">Add Code</button>
      </form>
    </div>
  );
}
