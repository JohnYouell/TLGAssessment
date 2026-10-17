import { Copy, Mail, MessageSquare, Users } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { trackShare } from "@/lib/useSharing";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

const buildMessage = (link) =>
  `Hey! I just completed the 7-part discipleship training series for 'The Lord's Gym: Discipleship Training, One Rep at a Time'. It has been an incredible tool for auditing my spiritual consistency and stepping out of the bleachers. I want to invite you to jump onto the training floor with me. Create your free account here to start Rep One: ${link}`;

const ShareAction = ({ icon: Icon, label, href, onClick, testId }) => {
  const cls = "flex flex-col items-center gap-2 rounded-sm border border-line bg-surface-2 px-3 py-4 text-xs uppercase tracking-widest text-zinc-200 transition-colors duration-150 hover:border-gold hover:text-gold";
  const inner = (<><Icon className="h-6 w-6 text-gold" />{label}</>);
  return href ? (
    <a href={href} onClick={onClick} className={cls} data-testid={testId}>{inner}</a>
  ) : (
    <button type="button" onClick={onClick} className={cls} data-testid={testId}>{inner}</button>
  );
};

export const TrainSomeoneNext = () => {
  const { user } = useAuth();
  const link = `${window.location.origin}/register?ref=${user.id}`;
  const message = buildMessage(link);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link);
      trackShare("train", "copy");
      toast.success("Invite link copied");
    } catch (e) {
      toast.error("Could not copy. Please copy the link manually.");
    }
  };
  const subject = encodeURIComponent("Join me on the training floor at The Lord's Gym");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button type="button" className="inline-flex items-center gap-2 rounded-sm border-2 border-gold px-7 py-3 font-heading text-sm font-semibold uppercase tracking-[0.18em] text-gold transition-colors duration-150 hover:bg-gold hover:text-black" data-testid="train-someone-next-button">
          <Users className="h-4 w-4" /> Train Someone Next
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-lg border-gold/40 bg-ink text-white" data-testid="invite-modal">
        <DialogHeader>
          <p className="eyebrow">Invite a Training Partner</p>
          <DialogTitle className="font-heading text-3xl uppercase text-white">Train Someone Next</DialogTitle>
          <DialogDescription className="text-zinc-400">Share this message with a friend to start their journey.</DialogDescription>
        </DialogHeader>
        <p className="rounded-sm border border-line bg-surface p-4 text-sm leading-relaxed text-zinc-200" data-testid="invite-message">{message}</p>
        <div className="flex min-w-0 items-center gap-2 rounded-sm border border-line bg-surface-2 px-3 py-2">
          <span className="min-w-0 flex-1 truncate text-xs text-gold" data-testid="invite-link">{link}</span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <ShareAction icon={Copy} label="Copy Link" onClick={copy} testId="invite-copy-link" />
          <ShareAction icon={MessageSquare} label="Text / SMS" href={`sms:?&body=${encodeURIComponent(message)}`} onClick={() => trackShare("train", "sms")} testId="invite-share-sms" />
          <ShareAction icon={Mail} label="Email" href={`mailto:?subject=${subject}&body=${encodeURIComponent(message)}`} onClick={() => trackShare("train", "email")} testId="invite-share-email" />
        </div>
      </DialogContent>
    </Dialog>
  );
};
