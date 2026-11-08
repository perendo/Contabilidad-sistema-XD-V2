from ..repositories.modelo_347 import Modelo347Repository


class Modelo347Service:
    def __init__(self, repo: Modelo347Repository):
        self.repo = repo

    def compute(self, year: int, threshold: float, company_id):
        return self.repo.compute(year, threshold, company_id)
