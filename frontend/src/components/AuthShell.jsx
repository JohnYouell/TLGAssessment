export const AuthShell = ({ eyebrow, title, children, testId }) => (
  <div className="grid min-h-[calc(100vh-74px)] lg:grid-cols-2" data-testid={testId}>
    <div className="relative hidden lg:block">
      <img src="/auth.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
      <p className="absolute bottom-12 left-12 max-w-sm font-accent text-2xl text-white">
        "Train yourself to be godly." <span className="mt-2 block text-sm text-gold">1 Timothy 4:7</span>
      </p>
    </div>
    <div className="flex items-center px-5 py-16 sm:px-12">
      <div className="w-full max-w-md">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white">{title}</h1>
        <div className="mt-10">{children}</div>
      </div>
    </div>
  </div>
);
