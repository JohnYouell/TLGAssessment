import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowDown, ArrowLeft, ArrowUp, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Endorsements, LAYOUT_OPTIONS, SAMPLE_ENDORSEMENTS } from "@/components/Endorsements";

const IconBtn = ({ onClick, disabled, label, testId, children }) => (
  <button type="button" onClick={onClick} disabled={disabled} aria-label={label} data-testid={testId}
    className="rounded-sm border border-line p-2 text-zinc-300 transition-colors duration-150 hover:border-gold hover:text-gold disabled:opacity-30">{children}</button>
);

const Row = ({ e, idx, total, update, move, remove }) => (
  <div className="grid gap-3 border border-line bg-surface p-5 md:grid-cols-12" data-testid={`endorsement-row-${idx}`}>
    <span className="font-heading text-2xl font-bold text-gold md:col-span-1">{String(idx + 1).padStart(2, "0")}</span>
    <div className="space-y-3 md:col-span-9">
      <Textarea value={e.text} onChange={(ev) => update(idx, "text", ev.target.value)} maxLength={1200} rows={3} placeholder="Endorsement text" className="field h-auto" data-testid={`endorsement-text-${idx}`} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input value={e.name} onChange={(ev) => update(idx, "name", ev.target.value)} maxLength={100} placeholder="Name" className="field" data-testid={`endorsement-name-${idx}`} />
        <Input value={e.position} onChange={(ev) => update(idx, "position", ev.target.value)} maxLength={150} placeholder="Position (e.g. Senior Pastor, Church Name)" className="field" data-testid={`endorsement-position-${idx}`} />
      </div>
      <Textarea value={e.booksText} onChange={(ev) => update(idx, "booksText", ev.target.value)} rows={2} placeholder="Books they've authored (one per line, optional)" className="field h-auto" data-testid={`endorsement-books-${idx}`} />
    </div>
    <div className="flex gap-2 md:col-span-2 md:flex-col md:items-end">
      <IconBtn onClick={() => move(idx, -1)} disabled={idx === 0} label="Move up" testId={`endorsement-up-${idx}`}><ArrowUp className="h-4 w-4" /></IconBtn>
      <IconBtn onClick={() => move(idx, 1)} disabled={idx === total - 1} label="Move down" testId={`endorsement-down-${idx}`}><ArrowDown className="h-4 w-4" /></IconBtn>
      <IconBtn onClick={() => remove(idx)} label="Delete" testId={`endorsement-delete-${idx}`}><Trash2 className="h-4 w-4" /></IconBtn>
    </div>
  </div>
);

const toItems = (rows) => rows.map(({ booksText, ...r }) => ({ ...r, books: booksText.split("\n").map((b) => b.trim()).filter(Boolean) }));
const toRows = (items) => items.map((i) => ({ ...i, booksText: (i.books || []).join("\n") }));

export default function AdminEndorsements() {
  const { user } = useAuth();
  const [layout, setLayout] = useState("cards");
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/endorsements").then((r) => { setLayout(r.data.layout); setRows(toRows(r.data.items)); });
  }, []);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!rows) return <Loader />;

  const update = (i, k, v) => setRows((rs) => rs.map((r, j) => (j === i ? { ...r, [k]: v } : r)));
  const move = (i, d) => setRows((rs) => { const n = [...rs]; [n[i], n[i + d]] = [n[i + d], n[i]]; return n; });
  const remove = (i) => setRows((rs) => rs.filter((_, j) => j !== i));
  const add = () => setRows((rs) => [...rs, { text: "", name: "", position: "", booksText: "" }]);

  const save = async () => {
    if (rows.some((r) => !r.text.trim() || !r.name.trim())) {
      toast.error("Every endorsement needs text and a name.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.put("/admin/endorsements", { layout, items: toItems(rows) });
      setRows(toRows(data.items));
      toast.success("Endorsements saved");
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  const preview = rows.filter((r) => r.text.trim() && r.name.trim());
  return (
    <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-endorsements-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="admin-endorsements-back-link"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Endorsements</h1>
      <p className="mt-3 text-zinc-400">These appear below the blurb on the /book page, in this order. The section stays hidden until you save at least one.</p>

      <p className="eyebrow mt-10">Layout</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-3" data-testid="endorsement-layout-options">
        {LAYOUT_OPTIONS.map(([k, label, hint]) => (
          <button key={k} type="button" onClick={() => setLayout(k)} data-testid={`endorsement-layout-${k}`}
            className={`border p-4 text-left transition-colors duration-150 ${layout === k ? "border-gold bg-gold/10" : "border-line bg-surface hover:border-gold"}`}>
            <p className="font-heading uppercase tracking-wide text-white">{label}</p>
            <p className="mt-1 text-xs text-zinc-400">{hint}</p>
          </button>
        ))}
      </div>

      <div className="mt-10 space-y-4">
        {rows.map((e, i) => <Row key={i} e={e} idx={i} total={rows.length} update={update} move={move} remove={remove} />)}
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-6">
        <button type="button" onClick={add} disabled={rows.length >= 30} className="inline-flex items-center gap-2 rounded-sm border-2 border-gold px-6 py-3 font-heading text-sm uppercase tracking-[0.18em] text-gold transition-colors duration-150 hover:bg-gold hover:text-black disabled:opacity-40" data-testid="endorsement-add-button">
          <Plus className="h-4 w-4" /> Add Endorsement
        </button>
        <button type="button" onClick={save} disabled={busy} className="btn-gold" data-testid="endorsement-save-button">{busy ? "Saving..." : "Save Changes"}</button>
      </div>

      <div className="mt-16 border-t border-line pt-4" data-testid="endorsement-preview">
        <p className="text-xs uppercase tracking-widest text-zinc-500">Preview{preview.length ? "" : " (sample placeholders, not shown on the site)"}</p>
        <Endorsements layout={layout} items={preview.length ? preview : SAMPLE_ENDORSEMENTS} />
      </div>
    </div>
  );
}
