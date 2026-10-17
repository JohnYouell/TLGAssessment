import { Link } from "react-router-dom";

const linkCls = "font-heading text-sm uppercase tracking-[0.18em] text-white transition-colors duration-150 hover:text-gold";

export const Footer = () => (
  <footer className="border-t border-line bg-black px-5 py-10 sm:px-8" data-testid="site-footer">
    <div className="mx-auto flex max-w-7xl flex-col items-center gap-6">
      <nav className="flex flex-wrap items-center justify-center gap-x-10 gap-y-3" data-testid="footer-nav">
        <Link to="/about" className={linkCls} data-testid="footer-about-link">About</Link>
        <Link to="/contact" className={linkCls} data-testid="footer-contact-link">Contact</Link>
        <a href="mailto:support@newlifeokc.org?subject=The%20Lord's%20Gym%20Support" className={linkCls} data-testid="footer-support-link">Support</a>
      </nav>
      <p className="text-xs text-zinc-400" data-testid="footer-copyright">
        &copy; {new Date().getFullYear()} The Lord&apos;s Gym. All rights reserved.
      </p>
    </div>
  </footer>
);
