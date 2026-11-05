import csv
import io
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Invoice, ReceivedInvoice, User

router = APIRouter(tags=["exportar-iva"])

VAT_RATES = [Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")]


def _sanitize_cell(val):
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _compute_iva(db: Session, date_from: date | None, date_to: date | None):
    q_emitidas = db.query(Invoice)
    q_recibidas = db.query(ReceivedInvoice)
    if date_from is not None:
        q_emitidas = q_emitidas.filter(Invoice.date >= date_from)
        q_recibidas = q_recibidas.filter(ReceivedInvoice.date >= date_from)
    if date_to is not None:
        q_emitidas = q_emitidas.filter(Invoice.date <= date_to)
        q_recibidas = q_recibidas.filter(ReceivedInvoice.date <= date_to)

    emitidas = q_emitidas.all()
    recibidas = q_recibidas.all()

    iva_devengado = sum((inv.vat_amount for inv in emitidas), Decimal("0"))
    iva_deducible = sum((inv.vat_amount for inv in recibidas), Decimal("0"))
    saldo = iva_devengado - iva_deducible
    if saldo > 0:
        tipo_saldo = "a ingresar"
    elif saldo < 0:
        tipo_saldo = "a compensar"
    else:
        tipo_saldo = "neutro"

    breakdown = {}
    for rate in VAT_RATES:
        breakdown[str(rate)] = {
            "devengado": float(sum((inv.vat_amount for inv in emitidas if inv.vat_rate == rate), Decimal("0"))),
            "deducible": float(sum((inv.vat_amount for inv in recibidas if inv.vat_rate == rate), Decimal("0"))),
        }

    return {
        "date_from": date_from,
        "date_to": date_to,
        "iva_devengado": float(iva_devengado),
        "iva_deducible": float(iva_deducible),
        "saldo": float(saldo),
        "tipo_saldo": tipo_saldo,
        "breakdown": breakdown,
    }


def _csv_export(data):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Liquidación de IVA"])
    writer.writerow([f"Desde {data['date_from']} hasta {data['date_to']}"])
    writer.writerow([])
    writer.writerow(["Concepto", "Importe"])
    writer.writerow(["IVA devengado", data["iva_devengado"]])
    writer.writerow(["IVA deducible", data["iva_deducible"]])
    writer.writerow(["Saldo", data["saldo"]])
    writer.writerow(["Tipo saldo", data["tipo_saldo"]])
    writer.writerow([])
    writer.writerow(["Tipo IVA", "Devengado", "Deducible"])
    for rate, vals in data["breakdown"].items():
        writer.writerow([rate, vals["devengado"], vals["deducible"]])
    return buf.getvalue().encode("utf-8")


def _pdf_export(data):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, "Liquidación de IVA", ln=True, align="C")
    pdf.cell(0, 8, f"Desde {data['date_from']} hasta {data['date_to']}", ln=True, align="C")
    pdf.ln(4)

    pdf.cell(0, 8, f"IVA devengado: {data['iva_devengado']:.2f}", ln=True)
    pdf.cell(0, 8, f"IVA deducible: {data['iva_deducible']:.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo: {data['saldo']:.2f}", ln=True)
    pdf.cell(0, 8, f"Tipo saldo: {data['tipo_saldo']}", ln=True)
    pdf.ln(4)

    headers = ["Tipo IVA", "Devengado", "Deducible"]
    widths = [40, 40, 40]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, border=1, align="C")
    pdf.ln()
    for rate, vals in data["breakdown"].items():
        pdf.cell(widths[0], 8, str(rate), border=1)
        pdf.cell(widths[1], 8, f"{vals['devengado']:.2f}", border=1, align="R")
        pdf.cell(widths[2], 8, f"{vals['deducible']:.2f}", border=1, align="R")
        pdf.ln()

    return bytes(pdf.output())


def _xlsx_export(data):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "IVA"
    ws.append(["Liquidación de IVA"])
    ws.append([f"Desde {data['date_from']} hasta {data['date_to']}"])
    ws.append([])
    ws.append(["Concepto", "Importe"])
    ws.append(["IVA devengado", data["iva_devengado"]])
    ws.append(["IVA deducible", data["iva_deducible"]])
    ws.append(["Saldo", data["saldo"]])
    ws.append(["Tipo saldo", data["tipo_saldo"]])
    ws.append([])
    ws.append(["Tipo IVA", "Devengado", "Deducible"])
    for rate, vals in data["breakdown"].items():
        ws.append([_sanitize_cell(rate), vals["devengado"], vals["deducible"]])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _respond(data, format, filename):
    if format == "csv":
        content = _csv_export(data)
        return Response(content=content, media_type="text/csv; charset=utf-8",
                       headers={"Content-Disposition": f"attachment; filename={filename}.csv"})
    if format == "pdf":
        content = _pdf_export(data)
        return Response(content=content, media_type="application/pdf",
                       headers={"Content-Disposition": f"attachment; filename={filename}.pdf"})
    if format == "xlsx":
        content = _xlsx_export(data)
        return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"})
    return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Formato no soportado")


@router.get("/exportar-iva", status_code=status.HTTP_200_OK)
@router.get("/exportar-iva-liquidacion", status_code=status.HTTP_200_OK)
@router.get("/exportar-liquidacion-iva", status_code=status.HTTP_200_OK)
def exportar_iva(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    format: str = Query(default="csv", alias="format"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = _compute_iva(db, date_from, date_to)
    return _respond(data, format, "iva")
