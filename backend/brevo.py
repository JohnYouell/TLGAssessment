import base64
import logging
import os
from html import escape

import httpx

log = logging.getLogger(__name__)
BASE = "https://api.brevo.com/v3"


async def _post(path, payload):
    headers = {"accept": "application/json", "content-type": "application/json", "api-key": os.environ["BREVO_API_KEY"]}
    try:
        async with httpx.AsyncClient(base_url=BASE, headers=headers, timeout=15.0) as client:
            r = await client.post(path, json=payload)
            if r.status_code >= 400:
                log.warning("Brevo %s failed: %s %s", path, r.status_code, r.text[:300])
                return None
            log.info("Brevo %s ok: %s", path, r.status_code)
            return r.json() if r.content else {}
    except httpx.HTTPError as exc:
        log.warning("Brevo %s error: %s", path, type(exc).__name__)
        return None


async def create_contact(email, full_name):
    first, _, last = full_name.strip().partition(" ")
    payload = {
        "email": email,
        "attributes": {"FIRSTNAME": first, "LASTNAME": last, "OPT_IN": True},
        "listIds": [int(os.environ["BREVO_MARKETING_LIST_ID"])],
        "updateEnabled": True,
    }
    return await _post("/contacts", payload)


def _row(cells, bold=False, bg="#ffffff"):
    tds = "".join(
        f'<td style="padding:10px 12px;border-bottom:1px solid #e4e4e7;{"font-weight:700;" if bold else ""}{c[1]}">{c[0]}</td>'
        for c in cells
    )
    return f'<tr style="background:{bg}">{tds}</tr>'


def _change(v):
    if v > 0:
        return (f"&#9650; +{v}", "color:#16a34a;font-weight:700;")
    if v < 0:
        return (f"&#9660; {v}", "color:#dc2626;")
    return ("0", "color:#71717a;")


def scorecard_html(name, data):
    head = "".join(
        f'<th style="padding:10px 12px;text-align:left;font-size:11px;letter-spacing:2px;color:#D4AF37">{h}</th>'
        for h in ("SECTIONS", "CHAPTERS", "DAY 1", "TODAY", "CHANGE")
    )
    rows = "".join(
        _row([(escape(r["section"]), ""), (r["chapters"], "color:#71717a;"), (f'{r["day1"]} / {r["max"]}', ""),
              (f'{r["today"]} / {r["max"]}', ""), _change(r["change"])])
        for r in data["rows"]
    )
    t = data["total"]
    rows += _row([("TOTAL", ""), (f"Total out of {t['max']}", ""), (str(t["day1"]), ""), (str(t["today"]), ""),
                  _change(t["change"])], bold=True, bg="#f6efd9")
    return f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:0 auto;color:#0a0a0a">
<div style="background:#0a0a0a;padding:24px;border-bottom:3px solid #D4AF37">
<div style="color:#ffffff;font-size:20px;letter-spacing:2px;font-family:Georgia,serif">THE LORD'S GYM</div>
<div style="color:#D4AF37;font-size:11px;letter-spacing:2px;margin-top:4px">DISCIPLESHIP TRAINING, ONE REP AT A TIME</div></div>
<div style="padding:24px">
<h1 style="font-size:24px;margin:0 0 8px">Your Training Scorecard</h1>
<p style="color:#52525b;margin:0 0 20px">Well done, {escape(name)}. Here are your final Day 1 vs. Today results. Your printable scorecard is attached as a PDF.</p>
<table style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="background:#0a0a0a">{head}</tr></thead><tbody>{rows}</tbody></table>
<p style="margin:20px 0 4px;font-weight:700">Today: {escape(data["today_designation"])}</p>
<p style="margin:0;color:#52525b">{escape(data["today_meaning"])}</p>
<p style="margin-top:28px;text-align:center;color:#71717a;font-family:Georgia,serif">&ldquo;Train yourself to be godly.&rdquo; 1 Timothy 4:7</p>
</div></div>"""


P_STYLE = 'style="margin:0 0 18px;color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.65"'
BOOK = '<strong style="color:#D4AF37">The Lord\'s Gym: Discipleship Training, One Rep at a Time</strong>'


def _site(path):
    return f"{os.environ['SITE_URL'].rstrip('/')}{path}"


def branded_html(heading, paragraphs, cta_text, cta_url, logo=None, bg_url=None):
    logo = logo or os.environ["EMAIL_LOGO_URL"]
    bg_attr = f' background="{bg_url}"' if bg_url else ""
    bg_css = f"background-image:url('{bg_url}');background-size:cover;background-position:center;" if bg_url else ""
    divider = '<tr><td style="padding:0 40px"><div style="height:2px;background:#D4AF37;line-height:2px;font-size:0">&nbsp;</div></td></tr>'
    body = "".join(f"<p {P_STYLE}>{t}</p>" for t in paragraphs)
    return f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>@media only screen and (max-width:480px){{.cta{{font-size:14px !important;letter-spacing:1px !important;padding:16px 18px !important}}}}</style></head><body style="margin:0;padding:0;background:#0a0a0a">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"{bg_attr} style="background-color:#0a0a0a;{bg_css}"><tr><td align="center" style="padding:32px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{'rgba(10,10,10,0.72)' if bg_url else '#0a0a0a'};border:1px solid #2a2a2a">
<tr><td align="center" style="padding:40px 40px 28px"><img src="{logo}" alt="The Lord's Gym" width="140" style="display:block;width:140px;max-width:140px;height:auto;border:0"></td></tr>
{divider}
<tr><td style="padding:36px 40px 8px">
<h1 style="margin:0 0 24px;color:#ffffff;font-family:Georgia,'Times New Roman',serif;font-size:28px;letter-spacing:1px;text-align:center">{heading}</h1>
{body}
</td></tr>
<tr><td align="center" style="padding:16px 40px 40px">
<a href="{cta_url}" class="cta" style="display:inline-block;background:#D4AF37;color:#000000;font-family:Arial,Helvetica,sans-serif;font-size:16px;font-weight:900;letter-spacing:2px;text-decoration:none;padding:18px 32px;border-radius:2px">{cta_text}</a>
</td></tr>
{divider}
<tr><td align="center" style="padding:24px 40px 36px;color:#c0c0c8;font-family:Georgia,serif;font-size:13px;letter-spacing:2px">DISCIPLESHIP TRAINING, ONE REP AT A TIME</td></tr>
</table></td></tr></table></body></html>"""


def welcome_html():
    return branded_html(
        "Welcome to the Training Floor.",
        [
            f"You have successfully registered your account for {BOOK}. Your spiritual training regimen begins today. It is time to step out of the bleachers, face the weights, and commit to the daily work of growing in Christ.",
            "Your first assignment is waiting.",
        ],
        "START REP ONE", _site("/dashboard"),
    )


def reminder_html():
    return branded_html(
        "Don’t leave the weight on the rack.",
        [
            "Two days ago, you stepped onto the training floor at The Lord’s Gym. Spiritual growth doesn’t happen by sitting in the bleachers—it requires consistency, commitment, and putting in the daily work.",
            "Your training plan is waiting, and it’s time to complete your Initial Spiritual Assessment.",
        ],
        "FINISH YOUR FIRST REP", _site("/assessment/1"),
    )


async def _send(email, name, subject, html):
    payload = {
        "sender": {"name": os.environ["BREVO_SENDER_NAME"], "email": os.environ["BREVO_SENDER_EMAIL"]},
        "to": [{"email": email, "name": name}],
        "subject": subject,
        "htmlContent": html,
    }
    return await _post("/smtp/email", payload)


async def send_welcome_email(email, name):
    return await _send(email, name, "Welcome to the Training Floor", welcome_html())


async def send_reminder_email(email, name):
    return await _send(email, name, "Don’t leave the weight on the rack", reminder_html())


def nudge_html():
    return branded_html(
        "Consistency is where the growth happens.",
        [
            "You’ve already stepped onto the training floor and put in the reps on your discipleship journey. But spiritual strength isn’t built in a single workout—it’s forged through staying with the routine over the long haul.",
            "Don’t stop training partway through. Your next rep is waiting for you on the dashboard. Let’s finish the course and unlock your final Master Growth Review.",
        ],
        "RETURN TO THE TRAINING FLOOR", _site("/dashboard"),
        logo=_site("/email-logo-gold.png"), bg_url=_site("/email-texture.jpg"),
    )


async def send_nudge_email(email, name):
    return await _send(email, name, "Consistency is where the growth happens", nudge_html())


def completion_html(final_score, max_score):
    metric = (
        '<span style="display:block;margin:6px 0 0;padding:18px;border:2px solid #D4AF37;text-align:center">'
        '<span style="display:block;color:#D4AF37;font-size:12px;letter-spacing:3px;font-weight:700">YOUR FINAL TOTAL GROWTH SCORE</span>'
        f'<span style="display:block;color:#ffffff;font-family:Georgia,serif;font-size:44px;font-weight:700;line-height:1.2">{final_score}'
        f'<span style="color:#D4AF37;font-size:24px"> / {max_score}</span></span></span>'
    )
    return branded_html(
        'Course Completed.<br><span style="color:#D4AF37">You Finished the Work!</span>',
        [
            f"Congratulations! You have completed all 7 assessment stages of {BOOK}. You didn’t just stay in the bleachers—you stepped onto the floor, faced the weight, and committed to the daily work of growing in Christ.",
            f"Your Final Spiritual Training Metrics are locked in:{metric}",
            "Spiritual strength is a lifelong pursuit, and your training doesn’t end here. Keep clean form, stay on the floor, and look for who God is calling you to help train next.",
        ],
        "DOWNLOAD YOUR FINAL SCORECARD", _site("/master-results"),
        logo=_site("/email-logo-gold.png"), bg_url=_site("/email-texture.jpg"),
    )


async def send_completion_email(email, name, final_score, max_score):
    return await _send(email, name, "Course Completed. You Finished the Work!", completion_html(final_score, max_score))


def reset_html(token):
    return branded_html(
        "Reset your password.",
        [
            "We received a request to reset the password for your Lord’s Gym account. Click the button below to choose a new password. This link works once and expires in 1 hour.",
            "If you didn’t ask for this, you can safely ignore this email. Your password won’t change.",
        ],
        "RESET MY PASSWORD", _site(f"/reset-password?token={token}"),
    )


async def send_password_reset_email(email, name, token):
    return await _send(email, name, "Reset your Lord's Gym password", reset_html(token))


async def send_scorecard_email(email, name, data, pdf_bytes):
    payload = {
        "sender": {"name": os.environ["BREVO_SENDER_NAME"], "email": os.environ["BREVO_SENDER_EMAIL"]},
        "to": [{"email": email, "name": name}],
        "subject": "Your Lord's Gym Training Scorecard",
        "htmlContent": scorecard_html(name, data),
        "attachment": [{"content": base64.b64encode(pdf_bytes).decode("ascii"), "name": "Lords-Gym-Training-Scorecard.pdf"}],
    }
    return await _post("/smtp/email", payload)
