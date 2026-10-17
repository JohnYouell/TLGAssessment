import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const done = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const sessionId = new URLSearchParams(window.location.hash.slice(1)).get("session_id");
    const referred_by = sessionStorage.getItem("lg-ref");
    api.post("/auth/google", { session_id: sessionId, referred_by })
      .then(({ data }) => {
        sessionStorage.removeItem("lg-ref");
        setUser(data);
        navigate(data.is_new ? "/welcome" : "/dashboard", { replace: true });
      })
      .catch((e) => {
        window.history.replaceState(null, "", window.location.pathname);
        setError(formatApiError(e));
      });
  }, [navigate, setUser]);

  if (!error) return null;
  return (
    <div className="mx-auto max-w-md px-5 py-24 text-center" data-testid="auth-callback-error">
      <p className="text-zinc-300">{error}</p>
      <Link to="/login" className="btn-gold mt-8" data-testid="auth-callback-login-link">Back to Sign In</Link>
    </div>
  );
}
