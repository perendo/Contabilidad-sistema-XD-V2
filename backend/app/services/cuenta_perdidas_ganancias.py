from datetime import date

from ..repositories.cuenta_perdidas_ganancias import (
    CuentaPerdidasGananciasRepository,
)


class CuentaPerdidasGananciasService:
    def __init__(self, repo: CuentaPerdidasGananciasRepository):
        self.repo = repo

    def compute(self, company_id, date_from: date | None, date_to: date | None):
        return self.repo.compute(company_id, date_from, date_to)
