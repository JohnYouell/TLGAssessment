import { useState } from "react";
import { ChevronLeft, ChevronRight, Quote } from "lucide-react";

export const SAMPLE_ENDORSEMENTS = [
  { text: "[Placeholder endorsement] This book gave our small groups a clear, practical way to measure spiritual growth. The training language sticks, and people actually do the reps.", name: "[Pastor Name]", position: "[Senior Pastor, Church Name]", books: ["[Book Title One]", "[Book Title Two]"] },
  { text: "[Placeholder endorsement] Honest, encouraging and deeply biblical. A must-read for anyone who wants to move from the bleachers to the floor.", name: "[Reader Name]", position: "[Ministry Leader, City]", books: [] },
  { text: "[Placeholder endorsement] John writes like a coach who loves his team. Every chapter calls you to train, not just to try.", name: "[Author Name]", position: "[Author & Speaker]", books: ["[Book Title]"] },
];

const Books = ({ books, className = "" }) =>
  books?.length ? <p className={`mt-1 text-xs italic text-zinc-500 ${className}`}>Author of {books.join(", ")}</p> : null;

const Byline = ({ e }) => (
  <div>
    <p className="font-heading text-base uppercase tracking-wide text-white">{e.name}</p>
    {e.position && <p className="text-sm text-gold">{e.position}</p>}
    <Books books={e.books} />
  </div>
);

const Cards = ({ items }) => (
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-testid="endorsements-cards">
    {items.map((e, i) => (
      <figure key={i} className="flex flex-col justify-between border border-line bg-surface p-8 transition-colors duration-150 hover:border-gold" data-testid={`endorsement-${i}`}>
        <div>
          <Quote className="h-7 w-7 text-gold" />
          <blockquote className="mt-4 text-base leading-relaxed text-zinc-200">{e.text}</blockquote>
        </div>
        <figcaption className="mt-8 border-t border-line pt-5"><Byline e={e} /></figcaption>
      </figure>
    ))}
  </div>
);

const Spotlight = ({ items }) => {
  const [i, setI] = useState(0);
  const e = items[i % items.length];
  const go = (d) => setI((v) => (v + d + items.length) % items.length);
  return (
    <figure className="border border-line bg-surface px-6 py-12 text-center sm:px-16" data-testid="endorsements-spotlight">
      <Quote className="mx-auto h-10 w-10 text-gold" />
      <blockquote key={i} className="mx-auto mt-6 max-w-3xl animate-in fade-in font-accent text-xl leading-relaxed text-white sm:text-2xl" data-testid={`endorsement-${i}`}>{e.text}</blockquote>
      <div className="mx-auto mt-6 h-[4pt] w-16 bg-gold" />
      <figcaption className="mt-6"><Byline e={e} /></figcaption>
      {items.length > 1 && (
        <div className="mt-8 flex items-center justify-center gap-5">
          <button type="button" onClick={() => go(-1)} aria-label="Previous endorsement" className="rounded-sm border border-line p-2 text-zinc-300 transition-colors duration-150 hover:border-gold hover:text-gold" data-testid="endorsement-prev"><ChevronLeft className="h-4 w-4" /></button>
          <span className="text-xs tracking-widest text-zinc-500">{(i % items.length) + 1} / {items.length}</span>
          <button type="button" onClick={() => go(1)} aria-label="Next endorsement" className="rounded-sm border border-line p-2 text-zinc-300 transition-colors duration-150 hover:border-gold hover:text-gold" data-testid="endorsement-next"><ChevronRight className="h-4 w-4" /></button>
        </div>
      )}
    </figure>
  );
};

const List = ({ items }) => (
  <div className="space-y-10" data-testid="endorsements-list">
    {items.map((e, i) => (
      <figure key={i} className="grid gap-4 border-l-[4pt] border-gold pl-6 md:grid-cols-12 md:gap-10" data-testid={`endorsement-${i}`}>
        <figcaption className="md:col-span-4"><Byline e={e} /></figcaption>
        <blockquote className="text-base italic leading-relaxed text-zinc-200 md:col-span-8 md:text-lg">“{e.text}”</blockquote>
      </figure>
    ))}
  </div>
);

const LAYOUTS = { cards: Cards, spotlight: Spotlight, list: List };
export const LAYOUT_OPTIONS = [["cards", "Cards", "A grid of quote cards"], ["spotlight", "Spotlight", "One large quote at a time with arrows"], ["list", "Editorial List", "Stacked quotes with a gold rule"]];

export const Endorsements = ({ layout, items }) => {
  const Layout = LAYOUTS[layout] || Cards;
  return (
    <section className="mt-20" data-testid="endorsements-section">
      <p className="eyebrow">Praise for The Lord's Gym</p>
      <h2 className="mt-2 font-accent text-2xl font-bold text-white sm:text-3xl">What Leaders Are Saying</h2>
      <div className="mt-8"><Layout items={items} /></div>
    </section>
  );
};
