import { createContext, useContext, useState } from "react";
import { Check, Lock } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const PaywallContext = createContext(null);
const FEATURES = ["Section 1–5 Reviews (out of 75 each)", "Post-chapter video responses", "Final Assessment & Pastoral Briefing", "Master Results & growth profile", "Training videos library"];

const PaywallBody = ({ onDone }) => {
  const { reload } = useAuth();
  const [code, setCode] = useState("");
  const [quote, setQuote] = useState(null);
  const [busy, setBusy] = useState(false);
  const total = quote ? quote.total : 40;

  const apply = async () => {
    try {
      const { data } = await api.post("/payments/quote", { code });
      setQuote(data);
      toast.success(`Code applied: ${data.percent_off}% off`);
    } catch (e) {
      setQuote(null);
      toast.error(formatApiError(e));
    }
  };
  const buy = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/payments/checkout", { code: quote ? code : null, origin_url: window.location.origin });
      if (data.granted) {
        await reload();
        toast.success("Full Access unlocked. Welcome to the full program!");
        onDone();
        return;
      }
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error(formatApiError(e));
      setBusy(false);
    }
  };

  return (
    <div className="relative space-y-6">
      <DialogTitle className="font-accent text-2xl font-bold text-gold sm:text-3xl" data-testid="paywall-title">UNLOCK THE FULL TRAINING PROGRAM</DialogTitle>
      <DialogDescription className="text-zinc-200">Full Access to the assessment platform plus training videos, one package.</DialogDescription>
      <ul className="space-y-2 text-sm text-white">
        {FEATURES.map((f) => <li key={f} className="flex items-center gap-2"><Check className="h-4 w-4 text-gold" />{f}</li>)}
      </ul>
      <div className="flex items-end gap-3" data-testid="paywall-price">
        {quote && quote.percent_off > 0 && <span className="font-heading text-2xl text-zinc-500 line-through">$40.00</span>}
        <span className="font-heading text-5xl font-bold text-white">${total.toFixed(2)}</span>
        <span className="pb-1 text-xs uppercase tracking-widest text-zinc-400">one-time</span>
      </div>
      <div className="flex gap-2">
        <Input value={code} onChange={(e) => { setCode(e.target.value); setQuote(null); }} placeholder="Discount code" className="field" data-testid="paywall-code-input" />
        <button type="button" onClick={apply} disabled={!code.trim()} className="rounded-sm border-2 border-gold px-5 font-heading text-sm uppercase tracking-widest text-gold transition-colors duration-150 hover:bg-gold hover:text-black disabled:opacity-40" data-testid="paywall-apply-code-button">Apply</button>
      </div>
      <button type="button" onClick={buy} disabled={busy} className="btn-gold w-full justify-center" data-testid="paywall-purchase-button">
        <Lock className="h-4 w-4" /> {busy ? "Please wait..." : total <= 0 ? "Unlock Now" : `Get Full Access — $${total.toFixed(2)}`}
      </button>
    </div>
  );
};

export const PaywallProvider = ({ children }) => {
  const [open, setOpen] = useState(false);
  return (
    <PaywallContext.Provider value={{ openPaywall: () => setOpen(true) }}>
      {children}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg overflow-hidden border-gold/50 bg-black text-white" data-testid="paywall-modal">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-cover bg-center opacity-30" style={{ backgroundImage: "url(/email-texture.jpg)" }} />
          {open && <PaywallBody onDone={() => setOpen(false)} />}
        </DialogContent>
      </Dialog>
    </PaywallContext.Provider>
  );
};

export const usePaywall = () => useContext(PaywallContext);
