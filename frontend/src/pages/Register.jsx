import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { AuthShell } from "@/components/AuthShell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

const Field = ({ id, label, type = "text", value, onChange, testId, minLength }) => (
  <div className="space-y-2">
    <Label htmlFor={id} className="field-label">{label}</Label>
    <Input id={id} type={type} required minLength={minLength} value={value} onChange={(e) => onChange(e.target.value)} className="field" data-testid={testId} />
  </div>
);

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", marketing_opt_in: false });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      navigate("/welcome");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell eyebrow="Join the gym" title="Create Account" testId="register-page">
      <form onSubmit={submit} className="space-y-6">
        <Field id="name" label="Full Name" value={form.name} onChange={set("name")} testId="register-name-input" />
        <Field id="email" label="Email" type="email" value={form.email} onChange={set("email")} testId="register-email-input" />
        <Field id="password" label="Password (min 6 characters)" type="password" minLength={6} value={form.password} onChange={set("password")} testId="register-password-input" />
        <label htmlFor="optin" className="flex cursor-pointer items-start gap-3 text-sm text-zinc-300">
          <Checkbox id="optin" checked={form.marketing_opt_in} onCheckedChange={(v) => set("marketing_opt_in")(v === true)} className="mt-0.5 border-gold data-[state=checked]:bg-gold data-[state=checked]:text-black" data-testid="register-optin-checkbox" />
          <span>Yes, send me encouragement, training tips, and updates from The Lord's Gym by email.</span>
        </label>
        {error && <p className="text-sm text-red-400" data-testid="register-error">{error}</p>}
        <button type="submit" disabled={busy} className="btn-gold w-full justify-center" data-testid="register-submit-button">
          {busy ? "Creating account..." : "Create Account"}
        </button>
        <p className="text-sm text-zinc-400">
          Already training? <Link to="/login" className="text-link" data-testid="register-login-link">Sign in</Link>
        </p>
      </form>
    </AuthShell>
  );
}
