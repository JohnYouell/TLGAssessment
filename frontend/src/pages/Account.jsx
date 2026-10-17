import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

const Panel = ({ title, testId, children }) => (
  <section className="border border-line bg-surface p-6 sm:p-8" data-testid={testId}>
    <p className="eyebrow">{title}</p>
    <div className="mt-5 space-y-5">{children}</div>
  </section>
);

const Pref = ({ id, label, hint, checked, onChange }) => (
  <label htmlFor={id} className="flex cursor-pointer items-start justify-between gap-6">
    <span>
      <span className="block text-white">{label}</span>
      <span className="block text-sm text-zinc-400">{hint}</span>
    </span>
    <Switch id={id} checked={checked} onCheckedChange={onChange} className="data-[state=checked]:bg-gold data-[state=unchecked]:bg-zinc-600" data-testid={id} />
  </label>
);

const ProfilePanel = () => {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ name: user.name, marketing_opt_in: user.marketing_opt_in, reminders_opt_in: user.reminders_opt_in });
  const [busy, setBusy] = useState(false);
  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.put("/account", form);
      setUser(data);
      toast.success("Account updated");
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={save} className="space-y-6">
      <Panel title="Profile" testId="account-profile">
        <div className="space-y-2">
          <Label htmlFor="acc-name" className="field-label">Full Name</Label>
          <Input id="acc-name" required maxLength={100} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="field" data-testid="account-name-input" />
        </div>
        <div className="space-y-2">
          <Label className="field-label">Email</Label>
          <p className="text-zinc-300" data-testid="account-email">{user.email}</p>
        </div>
      </Panel>
      <Panel title="Email Preferences" testId="account-preferences">
        <Pref id="account-marketing-switch" label="Discipleship Training E-Marketing List" hint="News, resources and updates about The Lord's Gym." checked={form.marketing_opt_in} onChange={(v) => setForm({ ...form, marketing_opt_in: v })} />
        <Pref id="account-reminders-switch" label="Training Reminders" hint="The Day 2 reminder and a nudge if you pause partway through." checked={form.reminders_opt_in} onChange={(v) => setForm({ ...form, reminders_opt_in: v })} />
      </Panel>
      <button type="submit" disabled={busy} className="btn-gold" data-testid="account-save-button">{busy ? "Saving..." : "Save Changes"}</button>
    </form>
  );
};

const PasswordPanel = () => {
  const { user, setUser } = useAuth();
  const empty = { current_password: "", new_password: "", confirm: "" };
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const save = async (e) => {
    e.preventDefault();
    if (form.new_password !== form.confirm) {
      toast.error("New passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post("/account/password", { current_password: form.current_password, new_password: form.new_password });
      setUser(data);
      setForm(empty);
      toast.success("Password updated. Other devices have been signed out.");
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={save}>
      <Panel title={user.has_password ? "Change Password" : "Set a Password"} testId="account-password">
        {!user.has_password && <p className="text-sm text-zinc-400">You sign in with Google. Add a password to also sign in with your email.</p>}
        {user.has_password && (
          <div className="space-y-2">
            <Label htmlFor="acc-cur" className="field-label">Current Password</Label>
            <Input id="acc-cur" type="password" required value={form.current_password} onChange={set("current_password")} className="field" data-testid="account-current-password-input" />
          </div>
        )}
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="acc-new" className="field-label">New Password (min 6)</Label>
            <Input id="acc-new" type="password" required minLength={6} value={form.new_password} onChange={set("new_password")} className="field" data-testid="account-new-password-input" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="acc-conf" className="field-label">Confirm New Password</Label>
            <Input id="acc-conf" type="password" required minLength={6} value={form.confirm} onChange={set("confirm")} className="field" data-testid="account-confirm-password-input" />
          </div>
        </div>
        <button type="submit" disabled={busy} className="btn-gold" data-testid="account-password-button">{busy ? "Saving..." : "Update Password"}</button>
      </Panel>
    </form>
  );
};

const InvitesPanel = () => {
  const [d, setD] = useState(null);
  useEffect(() => {
    api.get("/account/invites").then((r) => setD(r.data)).catch(() => {});
  }, []);
  if (!d) return null;
  return (
    <Panel title="Your Invites" testId="account-invites">
      <div className="flex items-center gap-4">
        <Users className="h-8 w-8 text-gold" />
        <p className="font-heading text-xl uppercase text-white" data-testid="account-invites-summary">
          You've invited {d.shares} {d.shares === 1 ? "friend" : "friends"}, {d.joined} joined
        </p>
      </div>
      <p className="text-sm text-zinc-400">Counts come from Spread the Word and Train Someone Next. A friend "joined" when they create an account from your link.</p>
    </Panel>
  );
};

export default function Account() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-5 py-12 sm:px-8 lg:py-16" data-testid="account-page">
      <p className="eyebrow">Settings</p>
      <h1 className="font-heading text-4xl font-bold uppercase text-white sm:text-5xl">My Account</h1>
      <InvitesPanel />
      <ProfilePanel />
      <PasswordPanel />
    </div>
  );
}
