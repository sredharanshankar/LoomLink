"""A-M6: Packing list PDF (A4) for dispatches."""
from __future__ import annotations
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


def generate(dispatch: dict, mill: dict | None = None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    mill_name = (mill or {}).get("name", "Mill")
    mill_addr = (mill or {}).get("address_line1", "")
    mill_gstin = (mill or {}).get("gstin", "")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, h - 20 * mm, mill_name)
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 26 * mm, mill_addr)
    if mill_gstin:
        c.drawString(20 * mm, h - 31 * mm, f"GSTIN: {mill_gstin}")

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 40 * mm, "PACKING LIST")

    y = h - 50 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Dispatch No: {dispatch.get('code', '')}")
    dispatched = dispatch.get("dispatched_at") or ""
    c.drawString(110 * mm, y, f"Date: {dispatched[:10]}")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Buyer: {dispatch.get('buyer_name', '')}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Order: {dispatch.get('order_code', '')}")
    y -= 10 * mm

    items = dispatch.get("items", [])
    total_cm = dispatch.get("total_length_cm", sum(it.get("length_cm", 0) for it in items))

    data = [["#", "Roll Code", "Length (cm)"]]
    for i, item in enumerate(items, 1):
        data.append([str(i), item.get("roll_code", ""), str(item.get("length_cm", ""))])
    data.append(["", "TOTAL", str(total_cm)])

    col_widths = [15 * mm, 80 * mm, 40 * mm]
    row_h = 7 * mm

    table = Table(data, colWidths=col_widths, rowHeights=row_h)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d4a6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f5f5")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    table_w, table_h = table.wrapOn(c, w - 40 * mm, y)
    table.drawOn(c, 20 * mm, y - table_h)

    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 15 * mm, f"Total rolls: {len(items)}  |  Total length: {total_cm} cm")

    c.save()
    buf.seek(0)
    return buf.read()
