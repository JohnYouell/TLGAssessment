import { useEffect, useState } from "react";
import { UserRound } from "lucide-react";
import { api } from "@/lib/api";
import { Loader } from "@/components/Loader";

const PhotoPlaceholder = () => (
  <div className="flex aspect-[4/5] w-full max-w-[280px] flex-col items-center justify-center gap-3 rounded-sm border-2 border-dashed border-gold/60 bg-surface text-center" data-testid="about-photo-placeholder">
    <UserRound className="h-14 w-14 text-gold/70" />
    <span className="px-4 text-xs uppercase tracking-widest text-zinc-500">[Placeholder: author photo]</span>
  </div>
);

const AuthorPhoto = ({ url }) => {
  const [failed, setFailed] = useState(false);
  if (!url || failed) return <PhotoPlaceholder />;
  return (
    <img src={url} alt="Author" onError={() => setFailed(true)} className="aspect-[4/5] w-full max-w-[280px] rounded-sm border-2 border-gold object-cover" data-testid="about-author-photo" />
  );
};

export const usePage = (slug) => {
  const [page, setPage] = useState(null);
  useEffect(() => {
    api.get(`/pages/${slug}`).then((r) => setPage(r.data));
  }, [slug]);
  return page;
};

export const InfoPage = ({ slug, testId, children }) => {
  const page = usePage(slug);
  if (!page) return <Loader />;
  return (
    <div className="mx-auto max-w-3xl px-5 py-16 sm:px-8 lg:py-24" data-testid={testId}>
      {page.eyebrow && <p className="eyebrow" data-testid={`${slug}-eyebrow`}>{page.eyebrow}</p>}
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl lg:text-6xl" data-testid={`${slug}-title`}>{page.title}</h1>
      <div className="mt-6 h-[4pt] w-24 bg-gold" />
      {slug === "about" && <div className="mt-10"><AuthorPhoto url={page.photo_url} /></div>}
      <div className="mt-10 space-y-6 text-base leading-relaxed text-zinc-300 md:text-lg" data-testid={`${slug}-body`}>
        {page.body.split(/\n\s*\n/).map((para, i) => (
          <p key={i} className="whitespace-pre-line">{para}</p>
        ))}
        {children}
      </div>
    </div>
  );
};
