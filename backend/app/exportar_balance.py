def _sanitize_cell(val):
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s

import csv
import io
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from sqlalchemy import func

from .models import Account, JournalEntry, JournalLine, User

router = APIRouter(tags=["exportar-balance"])


def _compute_balance(db: Session, date_from: date | None, date_to: date | None, company_id: int | None = None):
    stmt = (
        db.query(
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalLine.debit), 0).label("total_debe"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("total_haber"),
        )
        .join(JournalLine, Account.id == JournalLine.account_id)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .filter(JournalEntry.status == "accepted")
        .filter(JournalEntry.company_id == company_id)
        .filter(Account.company_id == company_id)
    )
    if date_from is not None:
        stmt = stmt.filter(JournalEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.filter(JournalEntry.date <= date_to)

    rows_db = stmt.group_by(Account.id, Account.code, Account.name).order_by(Account.code).all()

    total_debe = Decimal("0")
    total_haber = Decimal("0")
    rows = []
    for code, name, debe, haber in rows_db:
        debe_dec = Decimal(str(debe))
        haber_dec = Decimal(str(haber))
        saldo = debe_dec - haber_dec
        total_debe += debe_dec
        total_haber += haber_dec
        rows.append({
            "code": code,
            "name": name,
            "debe": float(debe_dec),
            "haber": float(haber_dec),
            "saldo": float(saldo),
        })

    return rows, float(total_debe), float(total_haber)


def _csv_export(rows, total_debe, total_haber, date_from, date_to):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Cuenta", "Nombre", "Debe", "Haber", "Saldo"])
    for row in rows:
        writer.writerow([_sanitize_cell(row["code"]), _sanitize_cell(row["name"]), _sanitize_cell(row["debe"]), _sanitize_cell(row["haber"]), _sanitize_cell(row["saldo"])])
    writer.writerow([_sanitize_cell("TOTAL"), _sanitize_cell(""), _sanitize_cell(total_debe), _sanitize_cell(total_haber), _sanitize_cell(total_debe - total_haber)])
    return buf.getvalue().encode("utf-8")


def _pdf_export(rows, total_debe, total_haber, date_from, date_to):
    from fpdf import FPDF

    from datetime import datetime
    pdf = FPDF()
    pdf.set_creation_date(datetime(2020, 1, 1))
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, "Balance de sumas y saldos", ln=True, align="C")
    pdf.cell(0, 8, f"Desde {date_from} hasta {date_to}", ln=True, align="C")
    pdf.ln(4)

    headers = ["Cuenta", "Nombre", "Debe", "Haber", "Saldo"]
    widths = [25, 70, 30, 30, 30]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, border=1, align="C")
    pdf.ln()

    for row in rows:
        pdf.cell(widths[0], 8, str(row["code"]), border=1)
        pdf.cell(widths[1], 8, str(row["name"])[:30], border=1)
        pdf.cell(widths[2], 8, f"{row['debe']:.2f}", border=1, align="R")
        pdf.cell(widths[3], 8, f"{row['haber']:.2f}", border=1, align="R")
        pdf.cell(widths[4], 8, f"{row['saldo']:.2f}", border=1, align="R")
        pdf.ln()

    pdf.cell(widths[0], 8, "TOTAL", border=1)
    pdf.cell(widths[1], 8, "", border=1)
    pdf.cell(widths[2], 8, f"{total_debe:.2f}", border=1, align="R")
    pdf.cell(widths[3], 8, f"{total_haber:.2f}", border=1, align="R")
    pdf.cell(widths[4], 8, f"{total_debe - total_haber:.2f}", border=1, align="R")
    pdf.ln()

    return bytes(pdf.output())


def _xlsx_export(rows, total_debe, total_haber, date_from, date_to):
    from openpyxl import Workbook

    from datetime import datetime
    wb = Workbook()
    wb.properties.created = datetime(2020, 1, 1)
    wb.properties.modified = datetime(2020, 1, 1)
    ws = wb.active
    ws.title = "Balance"

    ws.append(["Balance de sumas y saldos"])
    ws.append([f"Desde {date_from} hasta {date_to}"])
    ws.append([])
    ws.append(["Cuenta", "Nombre", "Debe", "Haber", "Saldo"])
    for row in rows:
        ws.append([_sanitize_cell(row["code"]), _sanitize_cell(row["name"]), _sanitize_cell(row["debe"]), _sanitize_cell(row["haber"]), _sanitize_cell(row["saldo"])])
    ws.append([_sanitize_cell("TOTAL"), _sanitize_cell(""), _sanitize_cell(total_debe), _sanitize_cell(total_haber), _sanitize_cell(total_debe - total_haber)])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@router.get("/exportar-balance", status_code=status.HTTP_200_OK)
def exportar_balance(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    format: str = Query(default="csv", alias="format"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
):
    rows, total_debe, total_haber = _compute_balance(db, date_from, date_to, company_id)

    if format == "csv":
        content = _csv_export(rows, total_debe, total_haber, date_from, date_to)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="balance.csv"'},
        )
    if format == "pdf":
        content = _pdf_export(rows, total_debe, total_haber, date_from, date_to)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="balance.pdf"'},
        )
    if format == "xlsx":
        content = _xlsx_export(rows, total_debe, total_haber, date_from, date_to)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="balance.xlsx"'},
        )

    return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Formato no soportado")
