import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const VERSES = [
  { text: "Rather, train yourself to be godly.", ref: "1 Timothy 4:7" },
  { text: "Run in such a way as to get the prize.", ref: "1 Corinthians 9:24" },
  { text: "Let us run with perseverance the race marked out for us.", ref: "Hebrews 12:1" },
  { text: "I press on toward the goal to win the prize for which God has called me heavenward in Christ Jesus.", ref: "Philippians 3:14" },
  { text: "Those who hope in the Lord will renew their strength.", ref: "Isaiah 40:31" },
  { text: "Let us not become weary in doing good, for at the proper time we will reap a harvest if we do not give up.", ref: "Galatians 6:9" },
  { text: "I have fought the good fight, I have finished the race, I have kept the faith.", ref: "2 Timothy 4:7" },
];

export const ScriptureBanner = () => {
  const [i, setI] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setI((n) => (n + 1) % VERSES.length), 7000);
    return () => clearInterval(id);
  }, []);

  const v = VERSES[i];
  return (
    <section className="border-y border-gold/40 bg-black px-5 py-6 sm:px-8" data-testid="scripture-banner" aria-live="polite">
      <div className="mx-auto flex min-h-[88px] max-w-4xl items-center justify-center text-center sm:min-h-[48px]">
        <AnimatePresence mode="wait">
          <motion.p
            key={v.ref}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.5 }}
            className="font-accent text-sm text-white sm:text-base"
            data-testid="scripture-verse"
          >
            &ldquo;{v.text}&rdquo;
            <span className="ml-3 whitespace-nowrap font-heading text-xs uppercase tracking-[0.2em] text-gold" data-testid="scripture-reference">
              {v.ref} <span className="text-zinc-500">NIV</span>
            </span>
          </motion.p>
        </AnimatePresence>
      </div>
    </section>
  );
};
