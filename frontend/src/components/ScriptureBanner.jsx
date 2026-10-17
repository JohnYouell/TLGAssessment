import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export const ScriptureBanner = () => {
  const [verses, setVerses] = useState([]);
  const [i, setI] = useState(0);

  useEffect(() => {
    api.get("/verses").then((r) => setVerses(r.data.verses)).catch(() => {});
  }, []);

  useEffect(() => {
    if (verses.length < 2) {
      return undefined;
    }
    const id = setInterval(() => setI((n) => (n + 1) % verses.length), 7000);
    return () => clearInterval(id);
  }, [verses.length]);

  return (
    <section className="border-b border-t-[4pt] border-b-gold/40 border-t-gold bg-black px-5 py-6 sm:px-8" data-testid="scripture-banner" aria-live="polite">
      <div className="mx-auto grid min-h-[48px] max-w-4xl items-center text-center">
        {verses.map((v, idx) => (
          <p
            key={idx}
            aria-hidden={idx !== i}
            className={`font-accent text-sm text-white transition-opacity duration-700 ease-in-out [grid-area:1/1] sm:text-base ${idx === i ? "opacity-100" : "pointer-events-none opacity-0"}`}
            data-testid={idx === i ? "scripture-verse" : undefined}
          >
            &ldquo;{v.text}&rdquo;
            <span className="ml-3 whitespace-nowrap font-heading text-xs uppercase tracking-[0.2em] text-gold" data-testid={idx === i ? "scripture-reference" : undefined}>
              {v.ref} {v.translation && <span className="text-zinc-500">{v.translation}</span>}
            </span>
          </p>
        ))}
      </div>
    </section>
  );
};
