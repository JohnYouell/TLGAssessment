const MAP = {
  not_started: { label: "Not Started", cls: "border-zinc-600 text-zinc-400" },
  in_progress: { label: "In Progress", cls: "border-yellow-500 text-yellow-400" },
  completed: { label: "Completed", cls: "border-gold bg-gold text-black" },
};

export const StatusBadge = ({ status, testId }) => {
  const s = MAP[status] || MAP.not_started;
  return (
    <span data-testid={testId} className={`inline-flex items-center rounded-sm border px-2.5 py-1 font-heading text-[11px] uppercase tracking-[0.18em] ${s.cls}`}>
      {s.label}
    </span>
  );
};
