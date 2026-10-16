import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { AuthShell } from "@/components/AuthShell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell eyebrow="Welcome back" title="Sign In" testId="login-page">
      <form onSubmit={submit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email" className="field-label">Email</Label>
          <Input id="email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="field" data-testid="login-email-input" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password" className="field-label">Password</Label>
          <Input id="password" type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="field" data-testid="login-password-input" />
        </div>
        {error && <p className="text-sm text-red-400" data-testid="login-error">{error}</p>}
        <button type="submit" disabled={busy} className="btn-gold w-full justify-center" data-testid="login-submit-button">
          {busy ? "Signing in..." : "Sign In"}
        </button>
        <p className="text-sm text-zinc-400">
          New to the gym? <Link to="/register" className="text-link" data-testid="login-register-link">Create an account</Link>
        </p>
      </form>
    </AuthShell>
  );
}
