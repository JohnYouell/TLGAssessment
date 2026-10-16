from io import BytesIO
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ASSETS = Path(__file__).parent / "assets"
for _f in ("Oswald", "Cinzel", "Manrope"):
    pdfmetrics.registerFont(TTFont(_f, str(ASSETS / f"{_f}.ttf")))

INK = HexColor("#0A0A0A")
GOLD = HexColor("#B8932A")
GOLD_SOFT = HexColor("#F6EFD9")
GREY = HexColor("#6B6B70")
LINE = HexColor("#DADADD")
GREEN = HexColor("#16A34A")
RED = HexColor("#DC2626")

W, H = letter
M = 48


def _arrow(c, x, y, up):
    p = c.beginPath()
    if up:
        p.moveTo(x, y); p.lineTo(x + 8, y); p.lineTo(x + 4, y + 7)
    else:
        p.moveTo(x, y + 7); p.lineTo(x + 8, y + 7); p.lineTo(x + 4, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _change(c, x, y, v, size):
    color = GREEN if v > 0 else RED if v < 0 else GREY
    c.setFillColor(color)
    if v:
        _arrow(c, x, y, v > 0)
    c.setFont("Oswald", size)
    c.drawString(x + 13, y, f"+{v}" if v > 0 else str(v))


def _header(c, name, date_str):
    c.setFillColor(INK)
    c.rect(0, H - 110, W, 110, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 113, W, 3, fill=1, stroke=0)
    c.drawImage(str(ASSETS / "logo.png"), M, H - 96, width=66, height=82, mask="auto", preserveAspectRatio=True)
    c.setFillColor(white)
    c.setFont("Cinzel", 20)
    c.drawString(M + 82, H - 52, "THE LORD'S GYM")
    c.setFillColor(HexColor("#D4AF37"))
    c.setFont("Cinzel", 10.5)
    c.drawString(M + 83, H - 70, "DISCIPLESHIP TRAINING, ONE REP AT A TIME")
    c.setFillColor(INK)
    c.setFont("Oswald", 30)
    c.drawString(M, H - 168, "TRAINING SCORECARD")
    c.setFillColor(GREY)
    c.setFont("Manrope", 10.5)
    name = name if len(name) <= 40 else name[:39] + "…"
    c.drawString(M, H - 188, f"Athlete: {name}    |    Issued: {date_str}")
    c.drawRightString(W - M, H - 188, "Day 1 baseline vs. Today")


COLS = [("SECTIONS", M + 10), ("CHAPTERS", M + 228), ("DAY 1", M + 330), ("TODAY", M + 400), ("CHANGE", M + 462)]


def _table(c, data, top):
    row_h = 34
    c.setFillColor(INK)
    c.rect(M, top - 28, W - 2 * M, 28, fill=1, stroke=0)
    c.setFillColor(HexColor("#D4AF37"))
    c.setFont("Oswald", 10)
    for label, x in COLS:
        c.drawString(x, top - 18, label)
    y = top - 28
    for r in data["rows"]:
        y -= row_h
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(M, y, W - M, y)
        base = y + 13
        c.setFillColor(INK)
        c.setFont("Manrope", 10.5)
        c.drawString(COLS[0][1], base, r["section"])
        c.setFillColor(GREY)
        c.setFont("Manrope", 9.5)
        c.drawString(COLS[1][1], base, r["chapters"])
        c.setFillColor(INK)
        c.setFont("Oswald", 12)
        c.drawString(COLS[2][1], base, f"{r['day1']} / {r['max']}")
        c.drawString(COLS[3][1], base, f"{r['today']} / {r['max']}")
        _change(c, COLS[4][1], base, r["change"], 12)
    t = data["total"]
    c.setFillColor(GOLD_SOFT)
    c.rect(M, y - 40, W - 2 * M, 40, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(M, y - 2, W - 2 * M, 2, fill=1, stroke=0)
    base = y - 25
    c.setFillColor(INK)
    c.setFont("Oswald", 14)
    c.drawString(COLS[0][1], base, "TOTAL")
    c.setFont("Oswald", 10.5)
    c.drawString(COLS[1][1], base, f"TOTAL OUT OF {t['max']}")
    c.setFont("Oswald", 14)
    c.drawString(COLS[2][1], base, str(t["day1"]))
    c.drawString(COLS[3][1], base, str(t["today"]))
    _change(c, COLS[4][1], base, t["change"], 14)
    return y - 40


def _tiles(c, data, top):
    t = data["total"]
    gap = 12
    w = (W - 2 * M - 2 * gap) / 3
    tiles = [
        ("DAY 1 TOTAL", f"{t['day1']} / {t['max']}", data["day1_designation"]),
        ("TODAY TOTAL", f"{t['today']} / {t['max']}", data["today_designation"]),
        ("TOTAL GROWTH", f"+{t['change']}" if t["change"] > 0 else str(t["change"]), "points gained" if t["change"] > 0 else "keep pressing"),
    ]
    for i, (label, value, sub) in enumerate(tiles):
        x = M + i * (w + gap)
        c.setStrokeColor(INK if i < 2 else GOLD)
        c.setLineWidth(1.2)
        c.rect(x, top - 86, w, 86, fill=0, stroke=1)
        c.setFillColor(GOLD)
        c.setFont("Cinzel", 8.5)
        c.drawString(x + 14, top - 22, label)
        c.setFillColor(GREEN if i == 2 and t["change"] > 0 else INK)
        c.setFont("Oswald", 26)
        c.drawString(x + 14, top - 54, value)
        c.setFillColor(GREY)
        c.setFont("Manrope", 9.5)
        c.drawString(x + 14, top - 72, sub)
    return top - 86


def _footer(c, meaning, top):
    c.setFillColor(INK)
    c.setFont("Oswald", 11)
    c.drawString(M, top - 36, "WHAT YOUR TODAY SCORE MEANS")
    c.setFillColor(GREY)
    c.setFont("Manrope", 10)
    c.drawString(M, top - 53, meaning)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(M, 80, W - M, 80)
    c.setFillColor(INK)
    c.setFont("Cinzel", 10)
    c.drawCentredString(W / 2, 60, "\u201cTrain yourself to be godly.\u201d  1 Timothy 4:7")
    c.setFillColor(GREY)
    c.setFont("Manrope", 8)
    c.drawCentredString(W / 2, 44, "The Lord's Gym: Discipleship Training, One Rep at a Time")


def build_scorecard_pdf(name, date_str, data):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("The Lord's Gym - Training Scorecard")
    _header(c, name, date_str)
    bottom = _table(c, data, H - 215)
    tiles_bottom = _tiles(c, data, bottom - 28)
    _footer(c, data["today_meaning"], tiles_bottom)
    c.showPage()
    c.save()
    return buf.getvalue()
