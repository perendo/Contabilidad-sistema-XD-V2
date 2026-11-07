import csv
import io
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .modelo_347 import compute_modelo_347
from .models import User

router = APIRouter(tags=["exportar-modelo-347"])


def _sanitize_cell(val):
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _csv_export(data):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Modelo 347"])
    writer.writerow([f"Año {data['year']} - Umbral {data['threshold']}"])
    writer.writerow([])
    writer.writerow(["NIF/CIF", "Nombre", "Total anual"])
    for row in data["third_parties"]:
        writer.writerow([_sanitize_cell(row["tax_id"]), _sanitize_cell(row["name"]), _sanitize_cell(row["total_annual"])])
    return buf.getvalue().encode("utf-8")


def _pdf_export(data):
    from fpdf import FPDF
    from datetime import datetime
    pdf = FPDF()
    pdf.set_creation_date(datetime(2020, 1, 1))
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, "Modelo 347", ln=True, align="C")
    pdf.cell(0, 8, f"Año {data['year']} - Umbral {data['threshold']}", ln=True, align="C")
    pdf.ln(4)
    headers = ["NIF/CIF", "Nombre", "Total anual"]
    widths = [40, 90, 40]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, border=1, align="C")
    pdf.ln()
    for row in data["third_parties"]:
        pdf.cell(widths[0], 8, str(row["tax_id"]), border=1)
        pdf.cell(widths[1], 8, str(row["name"])[:40], border=1)
        pdf.cell(widths[2], 8, f"{row['total_annual']:.2f}", border=1, align="R")
        pdf.ln()
    return bytes(pdf.output())


def _xlsx_export(data):
    from openpyxl import Workbook
    from datetime import datetime
    wb = Workbook()
    wb.properties.created = datetime(2020, 1, 1)
    wb.properties.modified = datetime(2020, 1, 1)
    ws = wb.active
    ws.title = "Modelo 347"
    ws.append(["Modelo 347"])
    ws.append([f"Año {data['year']} - Umbral {data['threshold']}"])
    ws.append([])
    ws.append(["NIF/CIF", "Nombre", "Total anual"])
    for row in data["third_parties"]:
        ws.append([_sanitize_cell(row["tax_id"]), _sanitize_cell(row["name"]), _sanitize_cell(row["total_annual"])])
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


@router.get("/exportar-modelo-347", status_code=status.HTTP_200_OK)
@router.get("/exportar-347", status_code=status.HTTP_200_OK)
def exportar_modelo_347(
    year: int = Query(...),
    threshold: float = Query(ge=0),
    format: str = Query(default="csv", alias="format"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
):
    data = compute_modelo_347(db, year, threshold, company_id)
    return _respond(data, format, "modelo-347")
