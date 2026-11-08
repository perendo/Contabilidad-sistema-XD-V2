from datetime import date

from ..repositories.balance_sumas_saldos import BalanceSumasSaldosRepository


class BalanceSumasSaldosService:
    def __init__(self, repo: BalanceSumasSaldosRepository):
        self.repo = repo

    def compute(self, company_id, date_from: date | None, date_to: date | None):
        return self.repo.compute(company_id, date_from, date_to)
