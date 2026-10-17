import { Mail } from "lucide-react";
import { InfoPage } from "@/components/InfoPage";

export default function Contact() {
  return (
    <InfoPage slug="contact" testId="contact-page">
      <a href="mailto:support@newlifeokc.org?subject=The%20Lord's%20Gym%20Question" className="btn-gold" data-testid="contact-email-button">
        <Mail className="h-4 w-4" /> support@newlifeokc.org
      </a>
    </InfoPage>
  );
}
