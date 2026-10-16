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
- Brevo (backend/brevo.py, httpx): an opt-in signup creates a contact (FIRSTNAME, LASTNAME, OPT_IN=true) in list ID 2; downloading the scorecard also sends a transactional email with the HTML grid and the PDF attached. Both run in the background and never block the user. Sender: john.youell@newlifeokc.org as "The Lord's Gym"
- Header logo switched to the white TLG logo (public/logo-white.png)

## Assumptions
- A1's overall total uses the same /125 total tiers as A7
- Review tiers (A2-A6) reuse the same meaning text as the matching tier labels

## Backlog
- P1: Password reset
- P2: Printable/PDF master results, retake option, admin view of opt-ins
