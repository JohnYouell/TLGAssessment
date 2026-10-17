import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";

export function PaymentSuccess() {
  const [params] = useSearchParams();
  const { reload } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState("checking");

  useEffect(() => {
    const sid = params.get("session_id");
    let tries = 0;
    let timer;
    const poll = async () => {
      try {
        const { data } = await api.get(`/payments/status/${sid}`);
        if (data.payment_status === "paid") {
          await reload();
          setState("paid");
          return;
        }
      } catch (e) {
        setState("error");
        return;
      }
      tries += 1;
      if (tries < 15) timer = setTimeout(poll, 2000);
      else setState("timeout");
    };
    poll();
    return () => clearTimeout(timer);
  }, [params, reload]);

  if (state === "checking") return <Loader />;
  return (
    <div className="mx-auto max-w-2xl px-5 py-24 text-center" data-testid="payment-success-page">
      <h1 className="font-heading text-4xl font-bold uppercase text-white sm:text-5xl" data-testid="payment-status-title">
        {state === "paid" ? "Full Access Unlocked" : "We couldn't confirm your payment yet"}
      </h1>
      <p className="mt-4 text-zinc-400">{state === "paid" ? "Welcome to the full training program." : "If you were charged, please refresh in a minute or contact support@newlifeokc.org."}</p>
      <button type="button" onClick={() => navigate("/dashboard")} className="btn-gold mt-10" data-testid="payment-dashboard-button">Go to Dashboard</button>
    </div>
  );
}

export function PaymentCancel() {
  return (
    <div className="mx-auto max-w-2xl px-5 py-24 text-center" data-testid="payment-cancel-page">
      <h1 className="font-heading text-4xl font-bold uppercase text-white">Checkout canceled</h1>
      <p className="mt-4 text-zinc-400">No charge was made. You can unlock Full Access anytime from your dashboard.</p>
      <Link to="/dashboard" className="btn-gold mt-10" data-testid="payment-cancel-dashboard-button">Back to Dashboard</Link>
    </div>
  );
}
