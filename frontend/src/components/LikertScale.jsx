const LABELS = {
  1: "Rarely True",
  2: "Occasionally True",
  3: "Sometimes True",
  4: "Often True",
  5: "Consistently True under pressure",
};

export const LikertScale = ({ qid, value, onChange }) => (
  <div role="radiogroup" className="grid grid-cols-1 gap-2 sm:grid-cols-5" data-testid={`likert-${qid}`}>
    {[1, 2, 3, 4, 5].map((n) => {
      const active = value === n;
      return (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={active}
          onClick={() => onChange(n)}
          data-testid={`likert-${qid}-option-${n}`}
          className={`flex items-center gap-3 rounded-sm border px-4 py-3 text-left transition-colors duration-150 sm:flex-col sm:items-center sm:text-center ${
            active ? "border-gold bg-gold text-black" : "border-line bg-surface-2 text-zinc-300 hover:border-gold/60"
          }`}
        >
          <span className="font-heading text-2xl font-bold">{n}</span>
          <span className={`text-xs leading-tight ${active ? "text-black" : "text-zinc-400"}`}>{LABELS[n]}</span>
        </button>
      );
    })}
  </div>
);
