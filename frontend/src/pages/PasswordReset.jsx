import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { AuthShell } from "@/components/AuthShell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell eyebrow="Account help" title="Forgot Password" testId="forgot-page">
      {sent ? (
        <div className="space-y-6" data-testid="forgot-sent">
          <p className="text-zinc-300">If an account exists for <span className="text-white">{email}</span>, we've sent a link to reset your password. It expires in 1 hour.</p>
          <Link to="/login" className="text-link" data-testid="forgot-back-link">Back to Sign In</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-6">
          <p className="text-sm text-zinc-400">Enter your account email and we'll send you a reset link.</p>
          <div className="space-y-2">
            <Label htmlFor="email" className="field-label">Email</Label>
            <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="field" data-testid="forgot-email-input" />
          </div>
          {error && <p className="text-sm text-red-400" data-testid="forgot-error">{error}</p>}
          <button type="submit" disabled={busy} className="btn-gold w-full justify-center" data-testid="forgot-submit-button">{busy ? "Sending..." : "Send Reset Link"}</button>
          <Link to="/login" className="text-link inline-block text-sm" data-testid="forgot-login-link">Back to Sign In</Link>
        </form>
      )}
    </AuthShell>
  );
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [form, setForm] = useState({ password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const token = params.get("token");

  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setError("Passwords don't match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/auth/reset-password", { token, password: form.password });
      setUser(data);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(formatApiError(err));
      setBusy(false);
    }
  };

  if (!token) {
    return (
      <AuthShell eyebrow="Account help" title="Reset Password" testId="reset-page">
        <p className="text-zinc-300" data-testid="reset-missing-token">This reset link is incomplete. <Link to="/forgot-password" className="text-link">Request a new one</Link>.</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell eyebrow="Account help" title="Choose a New Password" testId="reset-page">
      <form onSubmit={submit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="password" className="field-label">New Password (min 6 characters)</Label>
          <Input id="password" type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="field" data-testid="reset-password-input" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm" className="field-label">Confirm New Password</Label>
          <Input id="confirm" type="password" required minLength={6} value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} className="field" data-testid="reset-confirm-input" />
        </div>
        {error && <p className="text-sm text-red-400" data-testid="reset-error">{error} {error.includes("expired") && <Link to="/forgot-password" className="text-link">Request a new link</Link>}</p>}
        <button type="submit" disabled={busy} className="btn-gold w-full justify-center" data-testid="reset-submit-button">{busy ? "Saving..." : "Save New Password"}</button>
      </form>
    </AuthShell>
  );
}
