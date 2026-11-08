from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import Account, JournalEntry, JournalLine


GRUPOS_PGC = {
    "1": "Financiación básica",
    "2": "Inmovilizado",
    "3": "Existencias",
    "4": "Cuentas comerciales",
    "5": "Cuentas financieras",
    "6": "Compras y gastos",
    "7": "Ventas e ingresos",
    "8": "Gastos e imputaciones",
    "9": "Ingresos e imputaciones",
}


class CuentaPerdidasGananciasRepository:
    def __init__(self, db: Session):
        self.db = db

    def compute(self, company_id, date_from: date | None, date_to: date | None):
        rows = (
            self.db.query(
                Account.code,
                Account.type,
                JournalLine.debit,
                JournalLine.credit,
            )
            .join(JournalLine, Account.id == JournalLine.account_id)
            .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
            .filter(JournalEntry.status == "accepted")
            .filter(Account.type.in_(("Ingreso", "Gasto")))
        )
        if company_id is not None:
            rows = rows.filter(
                JournalEntry.company_id == company_id,
                Account.company_id == company_id,
            )
        if date_from is not None:
            rows = rows.filter(JournalEntry.date >= date_from)
        if date_to is not None:
            rows = rows.filter(JournalEntry.date <= date_to)

        resultados = rows.all()

        total_ingresos = Decimal("0")
        total_gastos = Decimal("0")
        grupos_data: dict[str, Decimal] = {}
        for codigo, account_type, debit, credit in resultados:
            debit = Decimal(str(debit or 0))
            credit = Decimal(str(credit or 0))
            grupo = str(codigo)[0] if codigo else ""
            if account_type == "Ingreso":
                importe = credit - debit
                total_ingresos += importe
                signo = 1
            elif account_type == "Gasto":
                importe = debit - credit
                total_gastos += importe
                signo = -1
            else:
                importe = credit - debit
                signo = 1
            if grupo not in grupos_data:
                grupos_data[grupo] = Decimal("0")
            grupos_data[grupo] += importe * signo

        resultado_explotacion = (
            grupos_data.get("7", Decimal("0")) + grupos_data.get("6", Decimal("0"))
        )
        resultado_financiero = grupos_data.get("5", Decimal("0"))
        resultado_ejercicio = resultado_explotacion + resultado_financiero

        resultado = total_ingresos - total_gastos
        if resultado > 0:
            tipo_resultado = "beneficio"
        elif resultado < 0:
            tipo_resultado = "pérdida"
        else:
            tipo_resultado = "neutro"

        grupos = []
        for codigo in sorted(grupos_data.keys()):
            grupos.append(
                {
                    "codigo_grupo": codigo,
                    "nombre_grupo": GRUPOS_PGC.get(codigo, f"Grupo {codigo}"),
                    "importe": f"{grupos_data[codigo]:.2f}",
                }
            )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_ingresos": float(total_ingresos),
            "total_gastos": float(total_gastos),
            "resultado": float(resultado),
            "tipo_resultado": tipo_resultado,
            "grupos": grupos,
            "resultado_explotacion": float(resultado_explotacion),
            "resultado_financiero": float(resultado_financiero),
            "resultado_ejercicio": float(resultado_ejercicio),
        }
