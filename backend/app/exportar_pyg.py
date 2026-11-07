import csv
import io
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from .auth import get_current_user
from .database import get_db
from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["exportar-pyg"])


def _sanitize_cell(val):
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _compute_pyg(db: Session, date_from: date | None, date_to: date | None):
    rows = (
        db.query(
            Account.type,
            func.coalesce(func.sum(JournalLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("total_credit"),
        )
        .join(JournalLine, Account.id == JournalLine.account_id)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .filter(JournalEntry.status == "accepted")
        .filter(Account.type.in_(("Ingreso", "Gasto")))
    )
    if date_from is not None:
        rows = rows.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        rows = rows.filter(JournalEntry.date <= date_to)

    grouped = rows.group_by(Account.type).all()

    total_ingresos = Decimal("0")
    total_gastos = Decimal("0")
    for account_type, total_debit, total_credit in grouped:
        debit = Decimal(str(total_debit))
        credit = Decimal(str(total_credit))
        if account_type == "Ingreso":
            total_ingresos += credit - debit
        elif account_type == "Gasto":
            total_gastos += debit - credit

    resultado = total_ingresos - total_gastos
    if resultado > 0:
        tipo_resultado = "beneficio"
    elif resultado < 0:
        tipo_resultado = "pérdida"
    else:
        tipo_resultado = "neutro"

    return {
        "date_from": date_from,
        "date_to": date_to,
        "total_ingresos": float(total_ingresos),
        "total_gastos": float(total_gastos),
        "resultado": float(resultado),
        "tipo_resultado": tipo_resultado,
    }


def _csv_export(data):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Cuenta de pérdidas y ganancias"])
    writer.writerow([f"Desde {data['date_from']} hasta {data['date_to']}"])
    writer.writerow([])
    writer.writerow(["Concepto", "Importe"])
    writer.writerow([_sanitize_cell("Total ingresos"), _sanitize_cell(data["total_ingresos"])])
    writer.writerow([_sanitize_cell("Total gastos"), _sanitize_cell(data["total_gastos"])])
    writer.writerow([_sanitize_cell("Resultado"), _sanitize_cell(data["resultado"])])
    writer.writerow([_sanitize_cell("Tipo resultado"), _sanitize_cell(data["tipo_resultado"])])
    return buf.getvalue().encode("utf-8")


def _pdf_export(data):
    from fpdf import FPDF
    from datetime import datetime
    pdf = FPDF()
    pdf.set_creation_date(datetime(2020, 1, 1))
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, "Cuenta de pérdidas y ganancias", ln=True, align="C")
    pdf.cell(0, 8, f"Desde {data['date_from']} hasta {data['date_to']}", ln=True, align="C")
    pdf.ln(4)
    pdf.cell(0, 8, f"Total ingresos: {data['total_ingresos']:.2f}", ln=True)
    pdf.cell(0, 8, f"Total gastos: {data['total_gastos']:.2f}", ln=True)
    pdf.cell(0, 8, f"Resultado: {data['resultado']:.2f}", ln=True)
    pdf.cell(0, 8, f"Tipo: {data['tipo_resultado']}", ln=True)
    return bytes(pdf.output())


def _xlsx_export(data):
    from openpyxl import Workbook
    from datetime import datetime
    wb = Workbook()
    wb.properties.created = datetime(2020, 1, 1)
    wb.properties.modified = datetime(2020, 1, 1)
    ws = wb.active
    ws.title = "PyG"
    ws.append(["Cuenta de pérdidas y ganancias"])
    ws.append([f"Desde {data['date_from']} hasta {data['date_to']}"])
    ws.append([])
    ws.append(["Concepto", "Importe"])
    ws.append([_sanitize_cell("Total ingresos"), _sanitize_cell(data["total_ingresos"])])
    ws.append([_sanitize_cell("Total gastos"), _sanitize_cell(data["total_gastos"])])
    ws.append([_sanitize_cell("Resultado"), _sanitize_cell(data["resultado"])])
    ws.append([_sanitize_cell("Tipo resultado"), _sanitize_cell(data["tipo_resultado"])])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _respond(data, format, filename):
    if format == "csv":
        content = _csv_export(data)
        return Response(content=content, media_type="text/csv; charset=utf-8",
                       headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'})
    if format == "pdf":
        content = _pdf_export(data)
        return Response(content=content, media_type="application/pdf",
                       headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    if format == "xlsx":
        content = _xlsx_export(data)
        return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'})
    return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Formato no soportado")


@router.get("/exportar-pyg", status_code=status.HTTP_200_OK)
@router.get("/exportar-perdidas-ganancias", status_code=status.HTTP_200_OK)
@router.get("/exportar-cuenta-perdidas-ganancias", status_code=status.HTTP_200_OK)
def exportar_pyg(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    format: str = Query(default="csv", alias="format"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = _compute_pyg(db, date_from, date_to)
    return _respond(data, format, "pyg")
