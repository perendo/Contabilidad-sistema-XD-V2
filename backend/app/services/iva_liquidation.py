from datetime import date
from decimal import Decimal

from ..models import Invoice, ReceivedInvoice
from ..repositories.iva_liquidation import IVALiquidationRepository
from ..schemas.iva_liquidation import VAT_RATES


class IVALiquidationService:
    def __init__(self, repo: IVALiquidationRepository):
        self.repo = repo

    def compute(self, date_from: date | None, date_to: date | None, company_id):
        emitidas = self.repo.vat_totals(Invoice, company_id, date_from, date_to)
        recibidas = self.repo.vat_totals(
            ReceivedInvoice, company_id, date_from, date_to
        )
        iva_devengado = sum(emitidas.values(), Decimal("0"))
        iva_deducible = sum(recibidas.values(), Decimal("0"))
        saldo = iva_devengado - iva_deducible
        if saldo > 0:
            tipo_saldo = "a ingresar"
        elif saldo < 0:
            tipo_saldo = "a compensar"
        else:
            tipo_saldo = "neutro"

        breakdown = {
            str(rate): {
                "devengado": float(emitidas.get(rate, Decimal("0"))),
                "deducible": float(recibidas.get(rate, Decimal("0"))),
            }
            for rate in VAT_RATES
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
