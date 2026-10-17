import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowLeft, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

const DiscountInput = ({ kind, value, onKind, onValue, testId }) => (
  <div className="flex items-center gap-2">
    <select value={kind} onChange={(e) => onKind(e.target.value)} className="field h-10 rounded-sm border px-2 text-sm" data-testid={`${testId}-type`}>
      <option value="percent">% off</option>
      <option value="amount">$ off</option>
    </select>
    <Input type="number" min={kind === "amount" ? 0.01 : 1} max={kind === "amount" ? 25 : 100} step={kind === "amount" ? 0.01 : 1} value={value} onChange={(e) => onValue(e.target.value)} className="field w-24" data-testid={testId} />
  </div>
);

const payload = (kind, value) => (kind === "amount" ? { percent_off: 0, amount_off: Number(value) } : { percent_off: Number(value), amount_off: 0 });

const CodeRow = ({ c, onSave, onDelete }) => {
  const [kind, setKind] = useState(c.amount_off > 0 ? "amount" : "percent");
  const [val, setVal] = useState(c.amount_off > 0 ? c.amount_off : c.percent_off);
  return (
    <div className="grid items-center gap-3 border border-line bg-surface p-4 sm:grid-cols-12" data-testid={`code-row-${c.id}`}>
      <span className="font-heading text-lg uppercase tracking-wide text-white sm:col-span-4">{c.code}</span>
      <div className="sm:col-span-3">
        <DiscountInput kind={kind} value={val} onKind={setKind} onValue={setVal} testId={`code-percent-${c.id}`} />
      </div>
      <label className="flex items-center gap-2 text-sm text-zinc-300 sm:col-span-2">
        <Switch checked={c.active} onCheckedChange={(v) => onSave(c, payload(kind, val), v)} data-testid={`code-active-${c.id}`} /> {c.active ? "On" : "Off"}
      </label>
      <span className="text-xs text-zinc-500 sm:col-span-1">{c.uses} uses</span>
      <div className="flex gap-2 sm:col-span-2 sm:justify-end">
        <button type="button" onClick={() => onSave(c, payload(kind, val), c.active)} className="text-link text-sm" data-testid={`code-save-${c.id}`}>Save</button>
        <button type="button" onClick={() => onDelete(c)} aria-label="Delete" className="text-zinc-400 hover:text-red-400" data-testid={`code-delete-${c.id}`}><Trash2 className="h-4 w-4" /></button>
      </div>
    </div>
  );
};

export default function AdminCodes() {
  const { user } = useAuth();
  const [codes, setCodes] = useState(null);
  const [form, setForm] = useState({ code: "", kind: "percent", value: 10 });
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
  const save = (c, disc, active) => run(() => api.put(`/admin/codes/${c.id}`, { code: c.code, ...disc, active }), `${c.code} saved`);
  const del = (c) => window.confirm(`Delete code ${c.code}?`) && run(() => api.delete(`/admin/codes/${c.id}`), `${c.code} deleted`);
  const create = (e) => {
    e.preventDefault();
    run(() => api.post("/admin/codes", { code: form.code, ...payload(form.kind, form.value) }), "Code created").then(() => setForm({ code: "", kind: "percent", value: 10 }));
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-codes-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Discount Codes</h1>
      <p className="mt-3 text-zinc-400">Full Access is $25.00. Codes aren&apos;t case-sensitive and spaces are ignored. Each code takes either a percent or a dollar amount off. Codes that bring the price to $0 unlock access without checkout.</p>
      <div className="mt-10 space-y-3">{codes.map((c) => <CodeRow key={c.id} c={c} onSave={save} onDelete={del} />)}</div>
      <form onSubmit={create} className="mt-10 flex flex-wrap items-end gap-3 border-t border-line pt-8" data-testid="code-create-form">
        <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="New code name" required minLength={2} maxLength={40} className="field w-60" data-testid="code-new-name" />
        <DiscountInput kind={form.kind} value={form.value} onKind={(k) => setForm({ ...form, kind: k })} onValue={(v) => setForm({ ...form, value: v })} testId="code-new-percent" />
        <button type="submit" className="btn-gold" data-testid="code-create-button">Add Code</button>
      </form>
    </div>
  );
}
