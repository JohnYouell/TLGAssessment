import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const NavLinks = ({ onNavigate }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const handleSignOut = async () => {
    onNavigate();
    await logout();
    navigate("/");
  };
  if (!user) {
    return (
      <>
        <Link to="/login" onClick={onNavigate} className="nav-link" data-testid="nav-sign-in">Sign In</Link>
        <Link to="/register" onClick={onNavigate} className="nav-link" data-testid="nav-create-account">Create Account</Link>
      </>
    );
  }
  return (
    <>
      <Link to="/dashboard" onClick={onNavigate} className="nav-link" data-testid="nav-dashboard">Dashboard</Link>
      <Link to="/account" onClick={onNavigate} className="nav-link" data-testid="nav-account">My Account</Link>
      <button type="button" onClick={handleSignOut} className="nav-link text-left" data-testid="nav-sign-out">Sign Out</button>
    </>
  );
};

export const Header = () => {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  return (
    <header data-testid="site-header" className="site-header relative z-40 text-white">
      <div className="relative mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-[clamp(12px,1.6vw,25px)] sm:px-8">
        <Link to="/" className="flex min-w-0 items-center gap-3" data-testid="header-logo-link">
          <span className="logo-shine relative shrink-0" style={{ "--shine-mask": "url(/logo-gold-header.png)" }} data-testid="header-logo-wrap">
            <img src="/logo-gold-header.png" alt="The Lord's Gym logo" className="block h-auto max-h-[clamp(60px,8.5vw,140px)] w-auto" data-testid="header-logo" />
          </span>
          <span className="byline text-[clamp(0.75rem,1.6vw,1.3rem)] leading-tight" data-testid="header-byline">
            Discipleship Training,<br />One Rep at a Time
          </span>
        </Link>
        <nav className="hidden items-center gap-8 md:flex" data-testid="header-nav-desktop">
          <NavLinks onNavigate={close} />
        </nav>
        <button
          type="button"
          className="text-white md:hidden"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle menu"
          data-testid="header-hamburger-button"
        >
          {open ? <X className="h-7 w-7" /> : <Menu className="h-7 w-7" />}
        </button>
      </div>
      {open && (
        <nav className="relative flex flex-col gap-5 border-t border-white/10 px-5 py-6 md:hidden" data-testid="header-nav-mobile">
          <NavLinks onNavigate={close} />
        </nav>
      )}
    </header>
  );
};
