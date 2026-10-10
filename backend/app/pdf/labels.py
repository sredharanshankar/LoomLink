"""Label PDF generation: thermal (50×25 mm) and A4 sheet (3×8 grid).

QR code links to PUBLIC_BASE_URL/s/{code}.
Falls back gracefully if fonts not found (uses Helvetica).
"""
from __future__ import annotations
import io
import os
from typing import Sequence

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


_THERMAL_W = 50 * mm
_THERMAL_H = 25 * mm
_A4_COLS = 3
_A4_ROWS = 8
_A4_LABEL_W = A4[0] / _A4_COLS
_A4_LABEL_H = A4[1] / _A4_ROWS


def _get_qr_image(data: str) -> ImageReader:
    import qrcode
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _try_register_font(font_name: str, ttf_path: str) -> bool:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        if os.path.exists(ttf_path):
            pdfmetrics.registerFont(TTFont(font_name, ttf_path))
            return True
    except Exception:
        pass
    return False


def _setup_fonts() -> str:
    """Try to register DejaVuSans; return font name to use."""
    candidates = [
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans", "/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        ("NotoSans", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    ]
    for name, path in candidates:
        if _try_register_font(name, path):
            return name
    return "Helvetica"


_FONT: str | None = None


def _font() -> str:
    global _FONT
    if _FONT is None:
        _FONT = _setup_fonts()
    return _FONT


def _draw_label(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    code: str,
    qr_url: str,
    lines: list[str],
) -> None:
    font = _font()
    pad = 1.5 * mm
    qr_size = min(h - 2 * pad, w * 0.4)

    qr_img = _get_qr_image(qr_url)
    c.drawImage(qr_img, x + pad, y + pad, width=qr_size, height=qr_size)

    text_x = x + pad + qr_size + pad
    text_w = w - (pad + qr_size + pad) - pad

    c.setFont(font, 7)
    c.drawString(text_x, y + h - pad - 5, code)

    c.setFont(font, 5.5)
    line_h = 4.5
    ty = y + h - pad - 5 - line_h - 1
    for line in lines[:3]:
        if ty < y + pad:
            break
        # Truncate to fit width
        c.drawString(text_x, ty, line[:30])
        ty -= line_h


def thermal_pdf(
    public_base_url: str,
    code: str,
    lines: list[str],
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(_THERMAL_W, _THERMAL_H))
    qr_url = f"{public_base_url.rstrip('/')}/s/{code}"
    _draw_label(c, 0, 0, _THERMAL_W, _THERMAL_H, code, qr_url, lines)
    c.showPage()
    c.save()
    return buf.getvalue()


def a4_sheet_pdf(
    public_base_url: str,
    items: Sequence[tuple[str, list[str]]],
) -> bytes:
    """Generate an A4 sheet with up to 24 labels (3 cols × 8 rows)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    page_h = A4[1]

    idx = 0
    while idx < len(items):
        for row in range(_A4_ROWS):
            for col in range(_A4_COLS):
                if idx >= len(items):
                    break
                code, lines = items[idx]
                idx += 1
                lx = col * _A4_LABEL_W
                ly = page_h - (row + 1) * _A4_LABEL_H
                qr_url = f"{public_base_url.rstrip('/')}/s/{code}"
                _draw_label(c, lx, ly, _A4_LABEL_W, _A4_LABEL_H, code, qr_url, lines)
            else:
                continue
            break
        if idx < len(items):
            c.showPage()
        else:
            break

    c.showPage()
    c.save()
    return buf.getvalue()
