# PRD: The Lord's Gym Assessment Series

## Original problem statement
Build a professional, secure web application for a 7-part assessment series accompanying the book "The Lord's Gym: Discipleship Training, One Rep at a Time." Clean, modern, athletic aesthetic. Header on every page: official logo (max-height 50px, left), byline "Discipleship Training, One Rep at a Time" (Cinzel, bold, small-caps, white), cover texture background (cover/center), white text, text-only nav links (logged out: Sign In / Create Account; logged in: Dashboard / Sign Out), white turning gold #D4AF37 on hover, white hamburger on mobile. Features: signup/login with marketing opt-in plus a welcome gateway; 1-5 Likert scale (Rarely True ... Consistently True under pressure); dashboard with 7 sequential assessments (Not Started / In Progress / Completed); per-assessment results (score, designation, meaning); Master Results page locked until all 7 are done, with a 5-column table (Sections, Chapters, Day 1 Score, Today Score, Change) plus a TOTAL row "Total out of 125", positive change shown in green with an up arrow. Mobile responsive, state retained.
Content update (verbatim from user): A1 Initial Spiritual Assessment (25 questions, 5 sections, each scored out of 25), A2-A6 Section One-Five Reviews (15 questions each, out of 75), A7 Spiritual Progress Assessment (reuses the A1 questions; tiers per section and on the total out of 125). Tiers: In the Bleachers / On the Floor / Pressing Forward / Training Others.
Assets: logo https://i.ibb.co/Ps47qfz7/The-Lord-s-Gym-Golden-Emblem.png, header background https://ibb.co/tTmB3vF4 (both saved locally in /frontend/public).

## Architecture
- FastAPI + MongoDB (users, progress, login_attempts, assessments seeded from backend/assessments_config.py on startup)
- JWT auth in httpOnly cookies (15 min access, 7 day refresh), bcrypt, per-email lockout
- React + Tailwind + shadcn; Oswald, Cinzel and Manrope fonts; dark and gold theme
- Answers autosave to backend (debounced) and to localStorage

## User personas
Readers of the book working through the discipleship assessments; small-group leaders.

## Implemented (2026-10-16)
- Auth (register with opt-in, login, logout, refresh), welcome gateway at / and /welcome after signup
- Dashboard with 7 sequential rep cards, status badges, rep progress bar, Master Results tile
- Quiz with section headers (A1/A7), Likert scale, autosave, submit gated until all questions are answered
- Result page: total, designation, meaning; per-section breakdown for A1/A7
- Master Results: locked overlay, then the Day 1 (A1) vs Today (A7) table, total out of 125, colored change arrows; mobile-friendly
- All 115 verbatim questions and tier rules hardcoded
- Signup checkbox "Opt-in to the Discipleship Training E-Marketing List" saved as boolean `marketing_opt_in` on the user, logged in the browser console and the backend log (Brevo sync to come; no internal email list)
- "Download Your Training Scorecard" on Master Results: a branded, print-friendly PDF (reportlab) from GET /api/master-results/scorecard
- Brevo (backend/brevo.py, httpx): an opt-in signup creates a contact (FIRSTNAME, LASTNAME, OPT_IN=true) in the list "discipleship training e-marketing" (ID 3); downloading the scorecard also sends a transactional email with the HTML grid and the PDF attached. Every new account gets a black-and-gold "Welcome to the Training Floor" email with a START REP ONE button linking to SITE_URL/dashboard (update SITE_URL on deploy). All Brevo calls run in the background and never block the user. Sender: john.youell@newlifeokc.org as "The Lord's Gym"
- Header logo switched to the white TLG logo (public/logo-white.png)
- Day 2 reminder: the hourly platform cron (.emergent/crons.yml, POST /api/cron/day2-reminder, Bearer WEBHOOK_CRON_SECRET, idempotent per run_id) emails readers whose account is 48+ hours old and who haven't completed A1. It is sent once per user (users.day2_reminder_sent_at), and the FINISH YOUR FIRST REP button links to /assessment/1. Login now returns users to the page they were trying to open.
- Unfinished journey nudge: the hourly cron (POST /api/cron/journey-nudge) emails readers who have completed 1–6 assessments and been inactive for 7+ days (users.last_activity_at is updated on login, answer saves and submits). It is sent once per inactive stretch (nudge_sent_at is cleared on new activity). The email uses the texture background, the gold logo and a RETURN TO THE TRAINING FLOOR button linking to /dashboard; the optimized images are served from SITE_URL (/email-texture.jpg, /email-logo-gold.png).
- Completion celebration: submitting A7 with all 7 completed immediately sends (in the background) a "Course Completed. You Finished the Work!" email with the A7 total out of 125 and a DOWNLOAD YOUR FINAL SCORECARD button linking to /master-results.
- Train Someone Next: an outlined gold button next to the scorecard download on Master Results opens an invite pop-up with the exact invite text, a unique link (/register?ref=<user id>, stored as users.referred_by on signup), and Copy Link / Text-SMS / Email shortcuts.
- Welcome page: a desktop hero image and a separate phone hero image (cropped and faded), a rotating scripture banner (verses from GET /api/verses, editable by admins at /admin/verses; admin = ADMIN_EMAILS env allow-list), and a site-wide copyright footer. The header bottom bar and the banner's top bar are 4pt gold; the banner's bottom line is 1px gold at 40%.
- Footer nav (About /about, Contact /contact, Support = mailto:support@newlifeokc.org) above the copyright line. The About and Contact pages are admin-editable at /admin/pages/about and /admin/pages/contact (eyebrow, title, body with blank-line paragraphs, plus a photo_url on About). With no photo link, About shows a dashed author-photo placeholder, and it falls back to the placeholder if the link breaks.

- 2026-10-17 Two-tier paywall: FREE = A1 + 17 Chapter Reviews (ids 101-117, PLACEHOLDER questions); PAID ($40 Stripe claimable sandbox, one-time) = Section Reviews 2-6 (each unlocks after its chapters), Final A7 (after all section reviews; pastor video gate), post-chapter videos, /videos, Master Results (+ chapter and section score lists). Discount codes in admin (/admin/codes): BeataTeam 100, EarlyAdopters 50, SeniorLeader 75, TLG Staff 100; a 100% code grants access without Stripe. Vimeo videos and headlines in admin (/admin/videos). Pages: /welcome thank-you video, /congrats/initial, /chapter/:n (video + Spread the Word + Join the Conversation), /spread-the-word (draft text), /payment/success and /payment/cancel. Header ~30% larger with responsive clamp sizing.

- 2026-10-17 Chapter Reviews removed (they live in the book, not in the 7 Reps). The app is now just the 7 Reps: A1 is free; A2–A6 open all at once for All-Access users; A7 opens after A2–A6. The /chapter/:n pages are gone, and the videos are now 5 Section Review wrap-ups (admin keys section_2..section_6) shown on each section result page with Spread the Word. Spread the Word and Join the Conversation also appear on /congrats/initial. The Chapter Reviews list was removed from Master Results.

## Assumptions
- A1's overall total uses the same /125 total tiers as A7
- Review tiers (A2-A6) reuse the same meaning text as the matching tier labels

## Backlog
- P1: Password reset
- P2: Printable/PDF master results, retake option, admin view of opt-ins
