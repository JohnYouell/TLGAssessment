export const InfoPage = ({ eyebrow, title, testId, children }) => (
  <div className="mx-auto max-w-3xl px-5 py-16 sm:px-8 lg:py-24" data-testid={testId}>
    <p className="eyebrow">{eyebrow}</p>
    <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl lg:text-6xl">{title}</h1>
    <div className="mt-6 h-[4pt] w-24 bg-gold" />
    <div className="mt-10 space-y-6 text-base leading-relaxed text-zinc-300 md:text-lg">{children}</div>
  </div>
);
