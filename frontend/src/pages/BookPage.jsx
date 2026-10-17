import { motion } from "framer-motion";
import { ArrowRight, BookOpen } from "lucide-react";
import { Link } from "react-router-dom";
import { useSharing } from "@/lib/useSharing";
import { Loader } from "@/components/Loader";

export default function BookPage() {
  const s = useSharing();
  if (!s) return <Loader />;
  return (
    <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 sm:px-8 md:grid-cols-12 lg:py-24" data-testid="book-page">
      <motion.img initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        src="/book-cover-placeholder.png" alt="The Lord's Gym book cover" className="mx-auto w-56 drop-shadow-[0_20px_40px_rgba(212,175,55,0.25)] sm:w-72 md:col-span-5" data-testid="book-cover" />
      <div className="md:col-span-7">
        <p className="eyebrow">The Book</p>
        <h1 className="mt-3 font-heading text-4xl font-bold uppercase leading-[0.95] text-white sm:text-5xl lg:text-6xl" data-testid="book-title">
          The Lord's Gym<br /><span className="text-gold">Discipleship Training, One Rep at a Time</span>
        </h1>
        <div className="mt-6 h-[4pt] w-24 bg-gold" />
        <p className="mt-6 max-w-xl text-base text-zinc-300 md:text-lg">Discipleship Training, One Rep at a Time. A book and 7-part assessment journey to help you grow in Christ.</p>
        <div className="mt-10 flex flex-wrap items-center gap-6">
          {s.book_url ? (
            <a href={s.book_url} target="_blank" rel="noopener noreferrer" className="btn-gold" data-testid="book-buy-button"><BookOpen className="h-4 w-4" /> Get the Book</a>
          ) : (
            <span className="inline-flex items-center gap-2 rounded-sm border border-line px-6 py-3 font-heading text-sm uppercase tracking-[0.18em] text-zinc-400" data-testid="book-coming-soon">Purchase link coming soon</span>
          )}
          <Link to="/register" className="text-link inline-flex items-center gap-2" data-testid="book-join-link">Start the assessments <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </div>
    </div>
  );
}
