import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowDown, ArrowLeft, ArrowUp, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const IconBtn = ({ onClick, disabled, label, testId, children }) => (
  <button type="button" onClick={onClick} disabled={disabled} aria-label={label} data-testid={testId}
    className="rounded-sm border border-line p-2 text-zinc-300 transition-colors duration-150 hover:border-gold hover:text-gold disabled:opacity-30">
    {children}
  </button>
);

const VerseRow = ({ v, idx, total, update, move, remove }) => (
  <div className="grid gap-3 border border-line bg-surface p-5 md:grid-cols-12" data-testid={`verse-row-${idx}`}>
    <span className="font-heading text-2xl font-bold text-gold md:col-span-1">{String(idx + 1).padStart(2, "0")}</span>
    <div className="space-y-3 md:col-span-9">
      <Textarea value={v.text} onChange={(e) => update(idx, "text", e.target.value)} maxLength={300} rows={2} placeholder="Verse text"
        className="field h-auto" data-testid={`verse-text-${idx}`} />
      <div className="grid grid-cols-3 gap-3">
        <Input value={v.ref} onChange={(e) => update(idx, "ref", e.target.value)} maxLength={60} placeholder="Reference (e.g. 1 Timothy 4:7)"
          className="field col-span-2" data-testid={`verse-ref-${idx}`} />
        <Input value={v.translation} onChange={(e) => update(idx, "translation", e.target.value)} maxLength={20} placeholder="NIV"
          className="field" data-testid={`verse-translation-${idx}`} />
      </div>
    </div>
    <div className="flex gap-2 md:col-span-2 md:flex-col md:items-end">
      <IconBtn onClick={() => move(idx, -1)} disabled={idx === 0} label="Move up" testId={`verse-up-${idx}`}><ArrowUp className="h-4 w-4" /></IconBtn>
      <IconBtn onClick={() => move(idx, 1)} disabled={idx === total - 1} label="Move down" testId={`verse-down-${idx}`}><ArrowDown className="h-4 w-4" /></IconBtn>
      <IconBtn onClick={() => remove(idx)} disabled={total === 1} label="Delete" testId={`verse-delete-${idx}`}><Trash2 className="h-4 w-4" /></IconBtn>
    </div>
  </div>
);

export default function AdminVerses() {
  const { user } = useAuth();
  const [verses, setVerses] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/verses").then((r) => setVerses(r.data.verses));
  }, []);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!verses) return <Loader />;

  const update = (i, k, val) => setVerses((vs) => vs.map((v, j) => (j === i ? { ...v, [k]: val } : v)));
  const move = (i, d) => setVerses((vs) => {
    const next = [...vs];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    return next;
  });
  const remove = (i) => setVerses((vs) => vs.filter((_, j) => j !== i));
  const add = () => setVerses((vs) => [...vs, { text: "", ref: "", translation: "NIV" }]);

  const save = async () => {
    if (verses.some((v) => !v.text.trim() || !v.ref.trim())) {
      toast.error("Every verse needs text and a reference.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.put("/admin/verses", { verses: verses.map((v) => ({ ...v, text: v.text.trim(), ref: v.ref.trim() })) });
      setVerses(data.verses);
      toast.success("Scripture banner updated");
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-verses-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="admin-verses-back-link"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Scripture Banner</h1>
      <p className="mt-3 text-zinc-400">These verses rotate on the welcome page every 7 seconds, in this order.</p>
      <div className="mt-10 space-y-4">
        {verses.map((v, i) => <VerseRow key={i} v={v} idx={i} total={verses.length} update={update} move={move} remove={remove} />)}
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-6">
        <button type="button" onClick={add} disabled={verses.length >= 30} className="inline-flex items-center gap-2 rounded-sm border-2 border-gold px-6 py-3 font-heading text-sm uppercase tracking-[0.18em] text-gold transition-colors duration-150 hover:bg-gold hover:text-black disabled:opacity-40" data-testid="verse-add-button">
          <Plus className="h-4 w-4" /> Add Verse
        </button>
        <button type="button" onClick={save} disabled={busy} className="btn-gold" data-testid="verse-save-button">{busy ? "Saving..." : "Save Changes"}</button>
      </div>
    </div>
  );
}
