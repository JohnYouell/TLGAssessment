import { FaFacebookF, FaInstagram, FaLinkedinIn, FaTiktok, FaXTwitter } from "react-icons/fa6";

const ParlerIcon = ({ className }) => (
  <span
    aria-hidden="true"
    className={`block bg-current ${className}`}
    style={{
      WebkitMask: "url(/parler-icon.png) center / contain no-repeat",
      mask: "url(/parler-icon.png) center / contain no-repeat",
    }}
  />
);

const LINKS = [
  { name: "Facebook", href: "https://facebook.com/johnyouell", Icon: FaFacebookF, id: "facebook" },
  { name: "Instagram", href: "https://instagram.com/johnyouell", Icon: FaInstagram, id: "instagram" },
  { name: "X", href: "https://x.com/johnyouell", Icon: FaXTwitter, id: "x" },
  { name: "TikTok", href: "https://tiktok.com/@johnyouelljr", Icon: FaTiktok, id: "tiktok" },
  { name: "LinkedIn", href: "https://www.linkedin.com/in/johnyouell/", Icon: FaLinkedinIn, id: "linkedin" },
  { name: "Parler", href: "https://app.parler.com/johnyouelljr", Icon: ParlerIcon, id: "parler" },
];

export const SocialLinks = () => (
  <div className="flex flex-wrap items-center justify-center gap-3" data-testid="footer-social-links">
    {LINKS.map(({ name, href, Icon, id }) => (
      <a
        key={id}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={name}
        title={name}
        data-testid={`social-${id}-link`}
        className="flex h-10 w-10 items-center justify-center rounded-full border border-gold/50 text-gold transition-colors duration-150 hover:border-gold hover:bg-gold hover:text-black"
      >
        <Icon className="h-4 w-4" />
      </a>
    ))}
  </div>
);
