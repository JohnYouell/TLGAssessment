import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const Field = ({ label, hint, children }) => (
  <label className="block space-y-2">
    <span className="eyebrow">{label}</span>
    {children}
    {hint && <span className="block text-xs text-zinc-500">{hint}</span>}
  </label>
);

export default function AdminSharing() {
  const { user } = useAuth();
  const [s, setS] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/sharing").then((r) => setS(r.data));
  }, []);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!s) return <Loader />;
  const set = (k) => (e) => setS((v) => ({ ...v, [k]: e.target.value }));

  const save = async () => {
    setBusy(true);
    try {
      const { data } = await api.put("/admin/sharing", s);
      setS(data);
      toast.success("Book & sharing settings saved");
    } catch (e) {
      toast.error(e.response?.status === 422 ? "Check the fields: the link must start with https:// and the subject and message can't be empty." : formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-sharing-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="admin-sharing-back-link"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Book & Sharing</h1>
      <div className="mt-10 space-y-8">
        <Field label="Book purchase link" hint="Used by the Read the Book box on the Welcome page and the Get the Book button on /book. The Spread the Word message always ends with your /book page link, which shows the cover preview card. Leave blank until the book is available.">
          <Input value={s.book_url} onChange={set("book_url")} placeholder="https://..." maxLength={500} className="field" data-testid="sharing-book-url-input" />
        </Field>
        <Field label="Email subject">
          <Input value={s.share_subject} onChange={set("share_subject")} maxLength={120} className="field" data-testid="sharing-subject-input" />
        </Field>
        <Field label="Spread the Word message">
          <Textarea value={s.share_message} onChange={set("share_message")} maxLength={2000} rows={7} className="field h-auto" data-testid="sharing-message-input" />
        </Field>
      </div>
      <button type="button" onClick={save} disabled={busy} className="btn-gold mt-8" data-testid="sharing-save-button">{busy ? "Saving..." : "Save Changes"}</button>
    </div>
  );
}
