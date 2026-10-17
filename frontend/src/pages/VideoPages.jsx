import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Megaphone, Users, Mail, MessageSquare, Copy } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { usePaywall } from "@/context/PaywallContext";
import { VideoEmbed } from "@/components/VideoEmbed";
import { Loader } from "@/components/Loader";
import { useSharing, shareBody, trackShare } from "@/lib/useSharing";

const useVideoData = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/videos").then((r) => setData(r.data));
  }, []);
  return data;
};

const Shell = ({ eyebrow, title, testId, children }) => (
  <div className="mx-auto max-w-4xl px-5 py-14 text-center sm:px-8 lg:py-20" data-testid={testId}>
    <p className="eyebrow">{eyebrow}</p>
    <h1 className="mt-3 font-accent text-3xl font-bold text-white sm:text-5xl" data-testid={`${testId}-title`}>{title}</h1>
    <div className="mx-auto mt-6 h-[4pt] w-24 bg-gold" />
    <div className="mt-10 space-y-10">{children}</div>
  </div>
);

export function ThankYou() {
  const v = useVideoData();
  const { user } = useAuth();
  if (!v) return <Loader />;
  return (
    <Shell eyebrow={`Welcome, ${user.name.split(" ")[0]}`} title={v.videos.registration_thanks.title || "Thank You for Joining The Lord's Gym"} testId="thank-you-page">
      <VideoEmbed url={v.videos.registration_thanks.url} label="Thank-you video placeholder" testId="thank-you-video" />
      <Link to="/assessment/1" className="btn-gold" data-testid="thank-you-start-button">Start the Initial Assessment <ArrowRight className="h-4 w-4" /></Link>
    </Shell>
  );
}

export const ShareActions = ({ hasAccess }) => {
  const { openPaywall } = usePaywall();
  return (
    <div className="flex flex-wrap justify-center gap-4">
      <Link to="/spread-the-word" className="inline-flex items-center gap-2 rounded-sm border-2 border-gold px-7 py-3 font-heading text-sm uppercase tracking-[0.18em] text-gold transition-colors duration-150 hover:bg-gold hover:text-black" data-testid="spread-the-word-button">
        <Megaphone className="h-4 w-4" /> Spread the Word
      </Link>
      {!hasAccess && <button type="button" onClick={openPaywall} className="btn-gold" data-testid="join-conversation-button"><Users className="h-4 w-4" /> Join the Conversation</button>}
    </div>
  );
};

export function InitialCongrats() {
  const v = useVideoData();
  if (!v) return <Loader />;
  return (
    <Shell eyebrow="Initial Assessment Complete" title={v.videos.initial_congrats.title || "Congratulations! Your Baseline Is Set."} testId="initial-congrats-page">
      <VideoEmbed url={v.videos.initial_congrats.url} label="Congratulations video placeholder" testId="initial-congrats-video" />
      <div className="flex flex-wrap justify-center gap-6">
        <Link to="/assessment/1/result" className="btn-gold" data-testid="initial-congrats-result-button">See My Results <ArrowRight className="h-4 w-4" /></Link>
        <Link to="/dashboard" className="text-link self-center" data-testid="initial-congrats-dashboard-link">Go to Dashboard</Link>
      </div>
      <ShareActions hasAccess={v.has_access} />
    </Shell>
  );
}

export function SectionVideo({ aid }) {
  const v = useVideoData();
  if (!v) return null;
  const vid = v.videos[`section_${aid}`];
  return (
    <div className="mt-12 space-y-6" data-testid="section-video-block">
      <p className="eyebrow">{vid.title || "Section Wrap-Up & What's Next"}</p>
      <VideoEmbed url={vid.url} label="Section review video placeholder" testId="section-video" />
      <ShareActions hasAccess={v.has_access} />
    </div>
  );
}

const OUTLINE = "inline-flex items-center gap-2 rounded-sm border-2 border-gold px-6 py-3 font-heading text-sm uppercase tracking-[0.18em] text-gold transition-colors duration-150 hover:bg-gold hover:text-black";

export function SpreadTheWord() {
  const s = useSharing();
  const { user } = useAuth();
  if (!s) return <Loader />;
  const body = shareBody(s, user?.id);
  const track = (ch) => user && trackShare("spread", ch);
  const copy = async () => {
    await navigator.clipboard.writeText(body);
    track("copy");
    toast.success("Message copied");
  };
  return (
    <Shell eyebrow="Spread the Word" title="Invite a Friend to Train" testId="spread-word-page">
      <p className="mx-auto max-w-2xl whitespace-pre-line break-words rounded-sm border border-line bg-surface p-6 text-left text-zinc-200" data-testid="spread-word-message">{body}</p>
      <div className="flex flex-wrap justify-center gap-4">
        <a href={`mailto:?subject=${encodeURIComponent(s.share_subject)}&body=${encodeURIComponent(body)}`} onClick={() => track("email")} className="btn-gold" data-testid="spread-word-email-button"><Mail className="h-4 w-4" /> Email a Friend</a>
        <a href={`sms:?&body=${encodeURIComponent(body)}`} onClick={() => track("sms")} className={OUTLINE} data-testid="spread-word-sms-button"><MessageSquare className="h-4 w-4" /> Text / SMS</a>
        <button type="button" onClick={copy} className={OUTLINE} data-testid="spread-word-copy-button"><Copy className="h-4 w-4" /> Copy Message</button>
      </div>
    </Shell>
  );
}

export function TrainingVideos() {
  const v = useVideoData();
  const { openPaywall } = usePaywall();
  if (!v) return <Loader />;
  return (
    <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8" data-testid="training-videos-page">
      <p className="eyebrow">All-Access</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl">Training Videos</h1>
      <div className="mt-10 grid gap-8 md:grid-cols-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <div key={n} className="space-y-3" data-testid={`training-video-${n}`}>
            <p className="font-heading uppercase tracking-wide text-white">{v.videos[`section_${n + 1}`].title || `Section ${n} Review Wrap-Up`}</p>
            <VideoEmbed url={v.videos[`section_${n + 1}`].url} label={`Section ${n} video placeholder`} locked={!v.has_access} onUnlock={openPaywall} testId={`training-video-${n}-player`} />
          </div>
        ))}
      </div>
    </div>
  );
}
