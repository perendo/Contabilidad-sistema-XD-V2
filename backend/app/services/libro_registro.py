from datetime import date

from ..repositories.libro_registro import LibroRegistroRepository


class LibroRegistroService:
    def __init__(self, repo: LibroRegistroRepository):
        self.repo = repo

    def _factura_a_fila(self, inv) -> dict:
        tp = inv.third_party
        return {
            "date": inv.date,
            "number": inv.number,
            "supplier_number": None,
            "third_party_id": tp.id,
            "third_party_tax_id": tp.tax_id,
            "third_party_name": tp.name,
            "description": inv.description,
            "base_amount": float(inv.base_amount),
            "vat_rate": float(inv.vat_rate),
            "vat_amount": float(inv.vat_amount),
            "irpf_rate": float(inv.irpf_rate) if inv.irpf_rate is not None else None,
            "irpf_amount": float(inv.irpf_amount) if inv.irpf_amount is not None else None,
            "total": float(inv.total),
        }

    def _recibida_a_fila(self, inv) -> dict:
        tp = inv.third_party
        return {
            "date": inv.date,
            "number": None,
            "supplier_number": inv.supplier_number,
            "third_party_id": tp.id,
            "third_party_tax_id": tp.tax_id,
            "third_party_name": tp.name,
            "description": inv.description,
            "base_amount": float(inv.base_amount),
            "vat_rate": float(inv.vat_rate),
            "vat_amount": float(inv.vat_amount),
            "irpf_rate": float(inv.irpf_rate) if inv.irpf_rate is not None else None,
            "irpf_amount": float(inv.irpf_amount) if inv.irpf_amount is not None else None,
            "total": float(inv.total),
        }

    def compute(self, company_id, year: int):
        emitidas = self.repo.emitidas(company_id, year)
        recibidas = self.repo.recibidas(company_id, year)
        emitidas_rows = [self._factura_a_fila(inv) for inv in emitidas]
        recibidas_rows = [self._recibida_a_fila(inv) for inv in recibidas]
        total_emitidas = sum((row["total"] for row in emitidas_rows), 0.0)
        total_recibidas = sum((row["total"] for row in recibidas_rows), 0.0)
        return {
            "year": year,
            "emitidas": emitidas_rows,
            "recibidas": recibidas_rows,
            "total_emitidas": total_emitidas,
            "total_recibidas": total_recibidas,
        }
