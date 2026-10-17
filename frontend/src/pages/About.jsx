import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { InfoPage } from "@/components/InfoPage";

export default function About() {
  return (
    <InfoPage eyebrow="About" title="The Lord's Gym" testId="about-page">
      <p>
        <em>The Lord&apos;s Gym: Discipleship Training, One Rep at a Time</em> treats spiritual growth like training: steady, daily work
        that builds strength over time. This site is the companion assessment series for the book.
      </p>
      <p>
        The series has 7 assessments. You start with the Initial Spiritual Assessment as your Day 1 baseline. Then you work through
        five section reviews that follow the book&apos;s chapters, and you finish with the Spiritual Progress Assessment. Your Master
        Results compare Day 1 to Today across all five sections, so you can see how far you&apos;ve come.
      </p>
      <p className="rounded-sm border border-dashed border-gold/50 p-4 text-sm text-zinc-400" data-testid="about-placeholder">
        [Placeholder: author bio, ministry background and where to buy the book]
      </p>
      <Link to="/register" className="btn-gold" data-testid="about-cta">Begin Your Training <ArrowRight className="h-4 w-4" /></Link>
    </InfoPage>
  );
}
