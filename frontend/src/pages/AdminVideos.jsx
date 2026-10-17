import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";
import { Input } from "@/components/ui/input";

const LABELS = {
  registration_thanks: "Thank-you page after registration",
  initial_congrats: "Congratulations page after the Initial Assessment",
  pastor_final: "Final Assessment: Pastor Speaks Here (must be watched to unlock questions)",
  ...Object.fromEntries([1, 2, 3, 4, 5].map((n) => [`section_${n + 1}`, `Section ${n} Review wrap-up (shown after the review)`])),
};

export default function AdminVideos() {
  const { user } = useAuth();
  const [videos, setVideos] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/videos").then((r) => setVideos(r.data.videos));
  }, []);

  if (!user.is_admin) return <Navigate to="/dashboard" replace />;
  if (!videos) return <Loader />;
  const set = (k, f) => (e) => setVideos((v) => ({ ...v, [k]: { ...v[k], [f]: e.target.value } }));

  const save = async () => {
    setBusy(true);
    try {
      const { data } = await api.put("/admin/videos", { videos });
      setVideos(data.videos);
      toast.success("Videos saved");
    } catch (e) {
      toast.error(e.response?.status === 422 ? "Video links must be Vimeo links like https://vimeo.com/123456789" : formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8 lg:py-16" data-testid="admin-videos-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm"><ArrowLeft className="h-4 w-4" /> Dashboard</Link>
      <p className="eyebrow mt-8">Admin</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Videos</h1>
      <p className="mt-3 text-zinc-400">Paste Vimeo links (e.g. https://vimeo.com/123456789). Leave blank to show a placeholder.</p>
      <div className="mt-10 space-y-4">
        {Object.keys(LABELS).map((k) => (
          <div key={k} className="grid gap-3 border border-line bg-surface p-4 md:grid-cols-12" data-testid={`video-row-${k}`}>
            <p className="text-sm text-zinc-300 md:col-span-4">{LABELS[k]}</p>
            <Input value={videos[k].title} onChange={set(k, "title")} placeholder="Headline (optional)" maxLength={120} className="field md:col-span-4" data-testid={`video-title-${k}`} />
            <Input value={videos[k].url} onChange={set(k, "url")} placeholder="https://vimeo.com/..." maxLength={300} className="field md:col-span-4" data-testid={`video-url-${k}`} />
          </div>
        ))}
      </div>
      <button type="button" onClick={save} disabled={busy} className="btn-gold mt-8" data-testid="videos-save-button">{busy ? "Saving..." : "Save Videos"}</button>
    </div>
  );
}
