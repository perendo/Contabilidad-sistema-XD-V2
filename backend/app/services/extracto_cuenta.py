from datetime import date
from decimal import Decimal

from ..repositories.extracto_cuenta import ExtractoCuentaRepository


class ExtractoCuentaService:
    def __init__(self, repo: ExtractoCuentaRepository):
        self.repo = repo

    def compute(
        self,
        account_id: int,
        company_id,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        account = self.repo.get_account(account_id, company_id)
        if account is None:
            return None
        lines = self.repo.movements(account_id, company_id, date_from, date_to)

        initial_balance = self.repo.initial_balance(account_id, company_id, date_from)

        movements = []
        running = initial_balance
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for line in lines:
            entry = line.entry
            debit = line.debit
            credit = line.credit
            running += debit - credit
            total_debit += debit
            total_credit += credit
            movements.append(
                {
                    "date": entry.date,
                    "entry_id": entry.id,
                    "entry_description": entry.description,
                    "description": line.description,
                    "debit": float(debit),
                    "credit": float(credit),
                    "running_balance": float(running),
                }
            )

        return {
            "account_id": account.id,
            "account_code": account.code,
            "account_name": account.name,
            "date_from": date_from,
            "date_to": date_to,
            "initial_balance": float(initial_balance),
            "movements": movements,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "final_balance": float(running),
        }
