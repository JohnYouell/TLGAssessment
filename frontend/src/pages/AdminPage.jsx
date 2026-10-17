import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const NAMES = { about: "About Page", contact: "Contact Page" };

export default function AdminPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [page, setPage] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setPage(null);
    api.get(`/pages/${slug}`).then((r) => setPage(r.data)).catch(() => {});
  }, [slug]);

  if (!user.is_admin || !NAMES[slug]) return <Navigate to="/dashboard" replace />;
  if (!page) return <Loader />;
  const set = (k) => (e) => setPage((p) => ({ ...p, [k]: e.target.value }));

  const save = async () => {
    if (!page.title.trim() || !page.body.trim()) {
      toast.error("Title and page text are required.");
      return;
    }
    if (page.photo_url && !/^https:\/\/\S+$/.test(page.photo_url.trim())) {
      toast.error("Photo link must start with https:// and contain no spaces.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.put(`/admin/pages/${slug}`, page);
      setPage(data);
      toast.success(`${NAMES[slug]} updated`);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-page-editor">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="admin-page-back-link"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">{NAMES[slug]}</h1>
      <p className="mt-3 text-zinc-400">Leave a blank line between paragraphs. The {slug === "contact" ? "email button" : "\u201cBegin Your Training\u201d button"} always appears below the text.</p>
      <div className="mt-10 space-y-6">
        <div className="space-y-2">
          <Label className="field-label">Small heading (gold label)</Label>
          <Input value={page.eyebrow} onChange={set("eyebrow")} maxLength={40} className="field" data-testid="page-eyebrow-input" />
        </div>
        <div className="space-y-2">
          <Label className="field-label">Page title</Label>
          <Input value={page.title} onChange={set("title")} maxLength={80} className="field" data-testid="page-title-input" />
        </div>
        <div className="space-y-2">
          <Label className="field-label">Page text</Label>
          <Textarea value={page.body} onChange={set("body")} maxLength={8000} rows={14} className="field h-auto leading-relaxed" data-testid="page-body-input" />
        </div>
        {slug === "about" && (
          <div className="space-y-2">
            <Label className="field-label">Author photo link (direct https:// image link, e.g. from i.ibb.co; leave blank for placeholder)</Label>
            <Input value={page.photo_url || ""} onChange={set("photo_url")} maxLength={500} placeholder="https://i.ibb.co/.../photo.jpg" className="field" data-testid="page-photo-url-input" />
            {page.photo_url && <img src={page.photo_url} alt="Preview" className="mt-3 h-40 w-32 rounded-sm border border-gold object-cover" data-testid="page-photo-preview" />}
          </div>
        )}
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-6">
        <button type="button" onClick={save} disabled={busy} className="btn-gold" data-testid="page-save-button">{busy ? "Saving..." : "Save Changes"}</button>
        <Link to={`/${slug}`} target="_blank" className="text-link inline-flex items-center gap-2 text-sm" data-testid="page-view-link">View page <ExternalLink className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
