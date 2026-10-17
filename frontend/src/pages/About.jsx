import { Link } from "react-router-dom";
import { ArrowRight, BookOpen } from "lucide-react";
import { InfoPage } from "@/components/InfoPage";

export default function About() {
  return (
    <InfoPage slug="about" testId="about-page">
      <div className="flex flex-wrap items-center gap-6 pt-2">
        <Link to="/book" className="btn-gold" data-testid="about-book-link"><BookOpen className="h-4 w-4" /> Get the Book</Link>
        <Link to="/register" className="text-link inline-flex items-center gap-2" data-testid="about-cta">Begin Your Training <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </InfoPage>
  );
}
