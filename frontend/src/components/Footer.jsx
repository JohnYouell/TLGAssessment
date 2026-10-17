export const Footer = () => (
  <footer className="border-t border-line bg-black px-5 py-8 sm:px-8" data-testid="site-footer">
    <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
      <p className="text-xs text-zinc-400" data-testid="footer-copyright">
        &copy; {new Date().getFullYear()} The Lord&apos;s Gym. All rights reserved.
      </p>
      <p className="byline text-xs text-zinc-500">Discipleship Training, One Rep at a Time</p>
    </div>
  </footer>
);
