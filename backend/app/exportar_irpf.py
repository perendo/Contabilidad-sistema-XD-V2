import csv
import io
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .auth import get_current_user
from .company_context import active_company_id_dep
from .database import get_db
from .irpf_summary import compute_irpf
from .models import User

router = APIRouter(tags=["exportar-irpf"])


def _sanitize_cell(val):
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _csv_export(data):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Resumen IRPF"])
    writer.writerow([f"Año {data['year']} - Trimestre {data['quarter']}"])
    writer.writerow([])
    writer.writerow(["Modelo 111 (retenciones practicadas)"])
    writer.writerow([_sanitize_cell("Base"), _sanitize_cell(data["modelo_111"]["base"])])
    writer.writerow([_sanitize_cell("Retenciones a ingresar"), _sanitize_cell(data["modelo_111"]["retenciones_a_ingresar"])])
    writer.writerow([_sanitize_cell("Facturas recibidas"), _sanitize_cell(data["facturas_recibidas_count"])])
    writer.writerow([])
    writer.writerow(["Pagos a cuenta 130 (retenciones soportadas)"])
    writer.writerow([_sanitize_cell("Base"), _sanitize_cell(data["pagos_a_cuenta_130"]["base"])])
    writer.writerow([_sanitize_cell("Retenciones soportadas"), _sanitize_cell(data["pagos_a_cuenta_130"]["retenciones_soportadas"])])
    writer.writerow([_sanitize_cell("Facturas emitidas"), _sanitize_cell(data["facturas_emitidas_count"])])
    return buf.getvalue().encode("utf-8")


def _pdf_export(data):
    from fpdf import FPDF
    from datetime import datetime
    pdf = FPDF()
    pdf.set_creation_date(datetime(2020, 1, 1))
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, "Resumen IRPF", ln=True, align="C")
    pdf.cell(0, 8, f"Año {data['year']} - Trimestre {data['quarter']}", ln=True, align="C")
    pdf.ln(4)
    pdf.cell(0, 8, "Modelo 111 (retenciones practicadas)", ln=True)
    pdf.cell(0, 8, f"Base: {data['modelo_111']['base']:.2f}", ln=True)
    pdf.cell(0, 8, f"Retenciones a ingresar: {data['modelo_111']['retenciones_a_ingresar']:.2f}", ln=True)
    pdf.cell(0, 8, f"Facturas recibidas: {data['facturas_recibidas_count']}", ln=True)
    pdf.ln(2)
    pdf.cell(0, 8, "Pagos a cuenta 130 (retenciones soportadas)", ln=True)
    pdf.cell(0, 8, f"Base: {data['pagos_a_cuenta_130']['base']:.2f}", ln=True)
    pdf.cell(0, 8, f"Retenciones soportadas: {data['pagos_a_cuenta_130']['retenciones_soportadas']:.2f}", ln=True)
    pdf.cell(0, 8, f"Facturas emitidas: {data['facturas_emitidas_count']}", ln=True)
    return bytes(pdf.output())


def _xlsx_export(data):
    from openpyxl import Workbook
    from datetime import datetime
    wb = Workbook()
    wb.properties.created = datetime(2020, 1, 1)
    wb.properties.modified = datetime(2020, 1, 1)
    ws = wb.active
    ws.title = "IRPF"
    ws.append(["Resumen IRPF"])
    ws.append([f"Año {data['year']} - Trimestre {data['quarter']}"])
    ws.append([])
    ws.append(["Modelo 111 (retenciones practicadas)"])
    ws.append([_sanitize_cell("Base"), _sanitize_cell(data["modelo_111"]["base"])])
    ws.append([_sanitize_cell("Retenciones a ingresar"), _sanitize_cell(data["modelo_111"]["retenciones_a_ingresar"])])
    ws.append([_sanitize_cell("Facturas recibidas"), _sanitize_cell(data["facturas_recibidas_count"])])
    ws.append([])
    ws.append(["Pagos a cuenta 130 (retenciones soportadas)"])
    ws.append([_sanitize_cell("Base"), _sanitize_cell(data["pagos_a_cuenta_130"]["base"])])
    ws.append([_sanitize_cell("Retenciones soportadas"), _sanitize_cell(data["pagos_a_cuenta_130"]["retenciones_soportadas"])])
    ws.append([_sanitize_cell("Facturas emitidas"), _sanitize_cell(data["facturas_emitidas_count"])])
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


@router.get("/exportar-irpf", status_code=status.HTTP_200_OK)
@router.get("/exportar-irpf-summary", status_code=status.HTTP_200_OK)
def exportar_irpf(
    year: int = Query(...),
    quarter: int = Query(ge=1, le=4),
    format: str = Query(default="csv", alias="format"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_id: int | None = Depends(active_company_id_dep),
):
    data = compute_irpf(db, year, quarter, company_id)
    return _respond(data, format, "irpf")
