"""A-M7: Payslip PDF (A4) for payroll runs."""
from __future__ import annotations
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _fmt(p: int) -> str:
    return f"Rs.{p // 100:,}.{p % 100:02d}"


def generate_payslip(data: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, h - 20 * mm, data.get("mill_name", "Mill"))
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 27 * mm, data.get("mill_address", ""))
    if data.get("mill_gstin"):
        c.drawString(20 * mm, h - 33 * mm, f"GSTIN: {data['mill_gstin']}")

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 45 * mm, "PAYSLIP")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 52 * mm, f"Period: {data.get('period', '')}")

    y = h - 65 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Employee: {data.get('worker_name', '')}")
    c.drawString(110 * mm, y, f"Code: {data.get('worker_code', '')}")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    if data.get("worker_department"):
        c.drawString(20 * mm, y, f"Department: {data['worker_department']}")
        y -= 7 * mm

    y -= 5 * mm
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Attendance")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, f"Days Present: {data.get('days_present', 0)}")
    c.drawString(90 * mm, y, f"Overtime: {data.get('overtime_minutes', 0)} min")
    if data.get("piece_cm"):
        y -= 7 * mm
        c.drawString(25 * mm, y, f"Piece Work: {data['piece_cm']} cm")

    y -= 10 * mm
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Earnings")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, "Gross Wages")
    c.drawRightString(w - 20 * mm, y, _fmt(data.get("gross_paise", 0)))

    y -= 10 * mm
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Deductions")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    for adv in data.get("advances", []):
        c.drawString(25 * mm, y, f"Advance {adv.get('date', '')}")
        c.drawRightString(w - 20 * mm, y, _fmt(adv.get("amount_paise", 0)))
        y -= 7 * mm

    y -= 5 * mm
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "NET PAY")
    c.drawRightString(w - 20 * mm, y, _fmt(data.get("net_paise", 0)))

    if data.get("paid_at"):
        y -= 10 * mm
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, f"Paid on: {str(data['paid_at'])[:10]}")

    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 15 * mm, "Computer-generated payslip — no signature required.")
    c.save()
    buf.seek(0)
    return buf.read()


def generate_batch(payslip_list: list[dict]) -> bytes:
    if not payslip_list:
        return generate_payslip({})
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    for i, data in enumerate(payslip_list):
        if i > 0:
            c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, h - 20 * mm, data.get("mill_name", "Mill"))
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(w / 2, h - 40 * mm, "PAYSLIP")
        c.setFont("Helvetica", 10)
        c.drawCentredString(w / 2, h - 47 * mm, f"Period: {data.get('period', '')}")
        y = h - 57 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, f"Employee: {data.get('worker_name', '')} ({data.get('worker_code', '')})")
        y -= 10 * mm
        c.setFont("Helvetica", 10)
        c.drawString(25 * mm, y, f"Days Present: {data.get('days_present', 0)}")
        y -= 7 * mm
        c.drawString(25 * mm, y, "Gross")
        c.drawRightString(w - 20 * mm, y, _fmt(data.get("gross_paise", 0)))
        y -= 7 * mm
        c.drawString(25 * mm, y, "Deductions")
        c.drawRightString(w - 20 * mm, y, _fmt(data.get("deductions_paise", 0)))
        y -= 7 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "NET PAY")
        c.drawRightString(w - 20 * mm, y, _fmt(data.get("net_paise", 0)))

    c.save()
    buf.seek(0)
    return buf.read()
