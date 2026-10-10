"""A-M8: GST invoice PDF (A4)."""
from __future__ import annotations
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


def _fmt(p: int) -> str:
    return f"Rs.{p // 100:,}.{p % 100:02d}"


def generate(invoice: dict, mill: dict | None = None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    mill_name = (mill or {}).get("name", "Mill")
    mill_addr = (mill or {}).get("address_line1", "")
    mill_gstin = (mill or {}).get("gstin", "")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, h - 20 * mm, mill_name)
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 27 * mm, mill_addr)
    if mill_gstin:
        c.drawString(20 * mm, h - 33 * mm, f"GSTIN: {mill_gstin}")

    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(w - 20 * mm, h - 20 * mm, "TAX INVOICE")

    y = h - 50 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Invoice No: {invoice.get('number', '')}")
    c.drawRightString(w - 20 * mm, y, f"Date: {invoice.get('issue_date', '')}")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Due Date: {invoice.get('due_date', '')}")
    c.drawRightString(w - 20 * mm, y, f"Order: {invoice.get('order_code', '')}")

    y -= 12 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Bill To:")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, invoice.get("buyer_name", ""))
    y -= 6 * mm
    if invoice.get("buyer_address"):
        c.drawString(25 * mm, y, invoice["buyer_address"])
        y -= 6 * mm
    if invoice.get("buyer_gstin"):
        c.drawString(25 * mm, y, f"GSTIN: {invoice['buyer_gstin']}")
        y -= 6 * mm

    y -= 8 * mm

    lines = invoice.get("lines", [])
    data = [["Description", "Qty (cm)", "Rate (Rs/m)", "Amount"]]
    for l in lines:
        data.append([
            l.get("description", ""),
            str(l.get("quantity_cm", "")),
            str(l.get("rate_paise_per_m", 0) // 100),
            _fmt(l.get("amount_paise", 0)),
        ])

    n = len(lines)
    data.append(["", "", "Subtotal", _fmt(invoice.get("subtotal_paise", 0))])
    gst_pct = invoice.get("gst_bp", 1200) / 100
    data.append(["", "", f"GST ({gst_pct:.0f}%)", _fmt(invoice.get("gst_paise", 0))])
    data.append(["", "", "TOTAL", _fmt(invoice.get("total_paise", 0))])

    col_widths = [90 * mm, 25 * mm, 30 * mm, 35 * mm]
    table = Table(data, colWidths=col_widths, rowHeights=7 * mm)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d4a6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("INNERGRID", (0, 0), (-1, n), 0.25, colors.grey),
        ("BOX", (0, 0), (-1, n), 0.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, n), [colors.white, colors.HexColor("#f5f5f5")]),
        ("FONTNAME", (0, n + 3), (-1, n + 3), "Helvetica-Bold"),
    ]))

    table_w, table_h = table.wrapOn(c, w - 40 * mm, y)
    table.drawOn(c, 20 * mm, y - table_h)

    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 15 * mm, "E. & O.E. — Subject to jurisdiction.")

    c.save()
    buf.seek(0)
    return buf.read()
