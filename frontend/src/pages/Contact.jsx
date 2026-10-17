import { Mail } from "lucide-react";
import { InfoPage } from "@/components/InfoPage";

export default function Contact() {
  return (
    <InfoPage eyebrow="Contact" title="Get in Touch" testId="contact-page">
      <p>Questions about the assessments, your account or the book? Send us an email and we&apos;ll get back to you.</p>
      <a href="mailto:support@newlifeokc.org?subject=The%20Lord's%20Gym%20Question" className="btn-gold" data-testid="contact-email-button">
        <Mail className="h-4 w-4" /> support@newlifeokc.org
      </a>
      <p className="rounded-sm border border-dashed border-gold/50 p-4 text-sm text-zinc-400" data-testid="contact-placeholder">
        [Placeholder: mailing address, phone number and office hours]
      </p>
    </InfoPage>
  );
}
