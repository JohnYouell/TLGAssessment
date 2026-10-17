import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
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

  const v = verses[i];
  return (
    <section className="border-y-[4pt] border-gold bg-black px-5 py-6 sm:px-8" data-testid="scripture-banner" aria-live="polite">
      <div className="mx-auto flex min-h-[88px] max-w-4xl items-center justify-center text-center sm:min-h-[48px]">
        <AnimatePresence mode="wait">
          {v && (
            <motion.p
              key={`${i}-${v.ref}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.5 }}
              className="font-accent text-sm text-white sm:text-base"
              data-testid="scripture-verse"
            >
              &ldquo;{v.text}&rdquo;
              <span className="ml-3 whitespace-nowrap font-heading text-xs uppercase tracking-[0.2em] text-gold" data-testid="scripture-reference">
                {v.ref} {v.translation && <span className="text-zinc-500">{v.translation}</span>}
              </span>
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
};
