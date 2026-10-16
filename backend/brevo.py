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


async def send_scorecard_email(email, name, data, pdf_bytes):
    payload = {
        "sender": {"name": os.environ["BREVO_SENDER_NAME"], "email": os.environ["BREVO_SENDER_EMAIL"]},
        "to": [{"email": email, "name": name}],
        "subject": "Your Lord's Gym Training Scorecard",
        "htmlContent": scorecard_html(name, data),
        "attachment": [{"content": base64.b64encode(pdf_bytes).decode("ascii"), "name": "Lords-Gym-Training-Scorecard.pdf"}],
    }
    return await _post("/smtp/email", payload)
