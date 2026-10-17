import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { InfoPage } from "@/components/InfoPage";

export default function About() {
  return (
    <InfoPage slug="about" testId="about-page">
      <Link to="/register" className="btn-gold" data-testid="about-cta">Begin Your Training <ArrowRight className="h-4 w-4" /></Link>
    </InfoPage>
  );
}
