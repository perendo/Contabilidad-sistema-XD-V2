from datetime import date
from decimal import Decimal

from ..models import Invoice, ReceivedInvoice
from ..repositories.irpf_summary import IRPFSummaryRepository


class IRPFSummaryService:
    def __init__(self, repo: IRPFSummaryRepository):
        self.repo = repo

    def compute(self, year: int, quarter: int, company_id):
        date_from, date_to = self.repo.quarter_dates(year, quarter)
        base_recibidas, retenciones_practicadas, count_recibidas = (
            self.repo.irpf_totals(ReceivedInvoice, company_id, date_from, date_to)
        )
        base_emitidas, retenciones_soportadas, count_emitidas = (
            self.repo.irpf_totals(Invoice, company_id, date_from, date_to)
        )

        return {
            "year": year,
            "quarter": quarter,
            "date_from": date_from,
            "date_to": date_to,
            "modelo_111": {
                "base": float(base_recibidas),
                "retenciones_a_ingresar": float(retenciones_practicadas),
            },
            "pagos_a_cuenta_130": {
                "base": float(base_emitidas),
                "retenciones_soportadas": float(retenciones_soportadas),
            },
            "facturas_emitidas_count": count_emitidas,
            "facturas_recibidas_count": count_recibidas,
        }
