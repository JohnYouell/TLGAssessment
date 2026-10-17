import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { useSharing } from "@/lib/useSharing";
import { Loader } from "@/components/Loader";
import { api } from "@/lib/api";
import { Endorsements } from "@/components/Endorsements";

export default function BookPage() {
  const s = useSharing();
  const [params] = useSearchParams();
  const ref = params.get("ref") || localStorage.getItem("lg-ref");
  const [endo, setEndo] = useState(null);
  useEffect(() => {
    if (params.get("ref")) localStorage.setItem("lg-ref", params.get("ref"));
  }, [params]);
  useEffect(() => {
    api.get("/endorsements").then((r) => setEndo(r.data)).catch(() => {});
  }, []);
  if (!s) return <Loader />;
  return (
    <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 lg:py-24" data-testid="book-page">
    <div className="grid items-center gap-12 md:grid-cols-12">
      <motion.img initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        src="/book-3d.webp" alt="The Lord's Gym book by John Youell, Jr." className="mx-auto w-60 sm:w-80 md:col-span-5 lg:w-96" data-testid="book-cover" />
      <div className="md:col-span-7">
        <p className="eyebrow">The Book</p>
        <h1 className="mt-3 font-heading text-4xl font-bold uppercase leading-[0.95] text-white sm:text-5xl lg:text-6xl" data-testid="book-title">
          The Lord's Gym<br /><span className="text-gold">Discipleship Training, One Rep at a Time</span>
        </h1>
        <div className="mt-6 h-[4pt] w-24 bg-gold" />
        <p className="mt-6 max-w-xl text-base leading-relaxed text-zinc-300 md:text-lg" data-testid="book-blurb">Most believers aren't rebellious. They're untrained. In <em>The Lord's Gym</em>, Pastor John Youell, Jr. draws on his own journey from the doctor's office to the gym floor to show how God builds mature disciples through resistance, community, daily discipline, and clean form. With an Initial Spiritual Assessment and a closing Spiritual Progress Check, it's a discipleship training plan, one rep at a time.</p>
        <div className="mt-10 flex flex-wrap items-center gap-6">
          {s.book_url ? (
            <a href={s.book_url} target="_blank" rel="noopener noreferrer" className="btn-gold" data-testid="book-buy-button"><BookOpen className="h-4 w-4" /> Get the Book</a>
          ) : (
            <span className="inline-flex items-center gap-2 rounded-sm border border-line px-6 py-3 font-heading text-sm uppercase tracking-[0.18em] text-zinc-400" data-testid="book-coming-soon">Purchase link coming soon</span>
          )}
          <Link to={ref ? `/register?ref=${encodeURIComponent(ref)}` : "/register"} className="text-link inline-flex items-center gap-2" data-testid="book-join-link">Start the assessments <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </div>
    </div>
      <section className="mt-20 grid items-center gap-8 border-t border-line pt-14 sm:grid-cols-12" data-testid="book-author">
        <img src="/author-photo.jpg" alt="John Youell, Jr." className="aspect-[4/5] w-40 rounded-sm border-2 border-gold object-cover sm:col-span-3 sm:w-full sm:max-w-[220px]" data-testid="book-author-photo" />
        <div className="sm:col-span-9">
          <p className="eyebrow">About the Author</p>
          <h2 className="mt-2 font-accent text-2xl font-bold text-white sm:text-3xl">John Youell, Jr.</h2>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-zinc-300" data-testid="book-author-bio">John Youell, Jr. is the Lead Pastor of New Life Church in Oklahoma City and the founder and CEO of KingdomWay, which equips people to advance God's kingdom in their everyday lives. A preacher's kid with more than 40 years of continuous ministry, he is a church planter, speaker, singer-songwriter, worship leader, recording artist, and podcaster. John is the author of <em>The Lord's Gym</em>. He and his wife, Shandra, have three grown children.</p>
          <Link to="/about" className="text-link mt-5 inline-flex items-center gap-2 text-sm" data-testid="book-author-more-link">More about John <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </section>
      {endo?.items.length > 0 && <Endorsements layout={endo.layout} items={endo.items} />}
    </div>
  );
}
