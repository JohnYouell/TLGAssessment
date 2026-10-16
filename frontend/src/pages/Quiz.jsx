import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { LikertScale } from "@/components/LikertScale";
import { Loader } from "@/components/Loader";

const SectionHeader = ({ s }) => (
  <div className="mb-10 border-l-2 border-gold pl-4 pt-4" data-testid={`quiz-section-header-${s.id}`}>
    <p className="eyebrow">Section {s.id} · {s.chapters}</p>
    <h2 className="mt-1 font-heading text-2xl uppercase text-white">{s.title}</h2>
  </div>
);

export default function Quiz() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const storageKey = `lg-answers-${user.id}-${id}`;
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const saveTimer = useRef(null);

  useEffect(() => {
    api.get(`/assessments/${id}`)
      .then(({ data }) => {
        const local = JSON.parse(localStorage.getItem(storageKey) || "{}");
        setQuiz(data);
        setAnswers({ ...data.answers, ...local });
      })
      .catch((e) => setError(formatApiError(e)));
  }, [id, storageKey]);

  useEffect(() => {
    return () => clearTimeout(saveTimer.current);
  }, []);

  const choose = (qid, v) => {
    const next = { ...answers, [qid]: v };
    setAnswers(next);
    localStorage.setItem(storageKey, JSON.stringify(next));
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      api.put(`/assessments/${id}/progress`, { answers: next }).catch(() => {});
    }, 400);
  };

  const submit = async () => {
    setBusy(true);
    clearTimeout(saveTimer.current);
    try {
      await api.post(`/assessments/${id}/submit`, { answers });
      localStorage.removeItem(storageKey);
      toast.success("Rep complete. Well done.");
      navigate(`/assessment/${id}/result`);
    } catch (e) {
      toast.error(formatApiError(e));
      setBusy(false);
    }
  };

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-5 py-20 text-center" data-testid="quiz-error">
        <p className="text-zinc-300">{error}</p>
        <Link to="/dashboard" className="text-link mt-6 inline-block" data-testid="quiz-error-back-link">Back to Dashboard</Link>
      </div>
    );
  }
  if (!quiz) return <Loader />;
  if (quiz.status === "completed") return <Navigate to={`/assessment/${id}/result`} replace />;

  const answered = quiz.questions.filter((q) => answers[q.id]).length;
  const total = quiz.questions.length;

  return (
    <div className="mx-auto max-w-4xl px-5 py-12 sm:px-8 lg:py-16" data-testid="quiz-page">
      <Link to="/dashboard" className="text-link inline-flex items-center gap-2 text-sm" data-testid="quiz-back-link">
        <ArrowLeft className="h-4 w-4" /> Dashboard
      </Link>
      <p className="eyebrow mt-8">Rep {quiz.id} of 7 · {quiz.subtitle}</p>
      <h1 className="mt-3 font-heading text-4xl font-bold uppercase text-white sm:text-5xl" data-testid="quiz-title">{quiz.title}</h1>
      <p className="mt-3 text-zinc-400">{quiz.description}</p>

      <div className="sticky top-0 z-30 -mx-5 mt-10 border-b border-line bg-ink/95 px-5 py-4 backdrop-blur sm:-mx-8 sm:px-8">
        <div className="flex items-center justify-between text-xs uppercase tracking-widest text-zinc-400">
          <span>Progress</span>
          <span data-testid="quiz-progress-text">{answered} / {total} answered</span>
        </div>
        <div className="mt-2 h-1 bg-white/10"><div className="h-1 bg-gold transition-[width] duration-300" style={{ width: `${(answered / total) * 100}%` }} /></div>
      </div>

      <ol className="mt-10 space-y-12">
        {quiz.questions.map((q, i) => (
          <li key={q.id} data-testid={`quiz-question-${q.id}`}>
            {q.section && (i === 0 || quiz.questions[i - 1].section !== q.section) && (
              <SectionHeader s={quiz.sections.find((s) => s.id === q.section)} />
            )}
            <div className="flex gap-4">
              <span className="font-heading text-xl font-bold text-gold">{String(i + 1).padStart(2, "0")}</span>
              <p className="text-base text-white md:text-lg">{q.text}</p>
            </div>
            <div className="mt-5"><LikertScale qid={q.id} value={answers[q.id]} onChange={(v) => choose(q.id, v)} /></div>
          </li>
        ))}
      </ol>

      <div className="mt-16 flex flex-col items-start gap-3 border-t border-line pt-10">
        <button type="button" disabled={busy || answered < total} onClick={submit} className="btn-gold disabled:cursor-not-allowed disabled:opacity-40" data-testid="quiz-submit-button">
          {busy ? "Scoring..." : "Complete Rep & See Result"}
        </button>
        {answered < total && <p className="text-xs text-zinc-500" data-testid="quiz-remaining-hint">Answer all {total} questions to submit. Your progress saves automatically.</p>}
      </div>
    </div>
  );
}
