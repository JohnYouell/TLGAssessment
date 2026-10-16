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


def welcome_html():
    dashboard = f"{os.environ['SITE_URL'].rstrip('/')}/dashboard"
    logo = os.environ["EMAIL_LOGO_URL"]
    divider = '<tr><td style="padding:0 40px"><div style="height:2px;background:#D4AF37;line-height:2px;font-size:0">&nbsp;</div></td></tr>'
    p = 'style="margin:0 0 18px;color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.65"'
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#0a0a0a">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a"><tr><td align="center" style="padding:32px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0a0a0a;border:1px solid #2a2a2a">
<tr><td align="center" style="padding:40px 40px 28px"><img src="{logo}" alt="The Lord's Gym" width="140" style="display:block;width:140px;max-width:140px;height:auto;border:0"></td></tr>
{divider}
<tr><td style="padding:36px 40px 8px">
<h1 style="margin:0 0 24px;color:#ffffff;font-family:Georgia,'Times New Roman',serif;font-size:28px;letter-spacing:1px;text-align:center">Welcome to the Training Floor.</h1>
<p {p}>You have successfully registered your account for <strong style="color:#D4AF37">The Lord's Gym: Discipleship Training, One Rep at a Time</strong>. Your spiritual training regimen begins today. It is time to step out of the bleachers, face the weights, and commit to the daily work of growing in Christ.</p>
<p {p}>Your first assignment is waiting.</p>
</td></tr>
<tr><td align="center" style="padding:16px 40px 40px">
<a href="{dashboard}" style="display:inline-block;background:#D4AF37;color:#000000;font-family:Arial,Helvetica,sans-serif;font-size:16px;font-weight:900;letter-spacing:3px;text-decoration:none;padding:18px 44px;border-radius:2px">START REP ONE</a>
</td></tr>
{divider}
<tr><td align="center" style="padding:24px 40px 36px;color:#a1a1aa;font-family:Georgia,serif;font-size:13px;letter-spacing:2px">DISCIPLESHIP TRAINING, ONE REP AT A TIME</td></tr>
</table></td></tr></table></body></html>"""


async def send_welcome_email(email, name):
    payload = {
        "sender": {"name": os.environ["BREVO_SENDER_NAME"], "email": os.environ["BREVO_SENDER_EMAIL"]},
        "to": [{"email": email, "name": name}],
        "subject": "Welcome to the Training Floor",
        "htmlContent": welcome_html(),
    }
    return await _post("/smtp/email", payload)


async def send_scorecard_email(email, name, data, pdf_bytes):
    payload = {
        "sender": {"name": os.environ["BREVO_SENDER_NAME"], "email": os.environ["BREVO_SENDER_EMAIL"]},
        "to": [{"email": email, "name": name}],
        "subject": "Your Lord's Gym Training Scorecard",
        "htmlContent": scorecard_html(name, data),
        "attachment": [{"content": base64.b64encode(pdf_bytes).decode("ascii"), "name": "Lords-Gym-Training-Scorecard.pdf"}],
    }
    return await _post("/smtp/email", payload)
