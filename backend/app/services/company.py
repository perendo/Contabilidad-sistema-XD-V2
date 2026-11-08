from decimal import Decimal

from ..models import Company
from ..pgc_seed import seed_pgc
from ..repositories.company import CompanyMembershipRepository, CompanyRepository
from ..schemas.company import CompanyIn


class CompanyService:
    def __init__(
        self,
        company_repo: CompanyRepository,
        membership_repo: CompanyMembershipRepository,
    ):
        self.company_repo = company_repo
        self.membership_repo = membership_repo

    def upsert_company(
        self,
        data: CompanyIn,
        current_user_id: int,
        company_id: int | None,
    ) -> Company:
        if data.approval_threshold is not None and data.approval_threshold <= 0:
            raise ValueError("El importe umbral debe ser positivo")

        if company_id is not None:
            company = self.company_repo.get_by_id(company_id)
        else:
            company = self.company_repo.get_any()

        if company is None:
            company = self.company_repo.create(data.model_dump())
            self.membership_repo.create(current_user_id, company.id)
        else:
            membership = self.membership_repo.get_for_user_and_company(
                current_user_id, company.id
            )
            if membership is None:
                self.membership_repo.create(current_user_id, company.id)
            company.name = data.name
            company.tax_id = data.tax_id
            company.address = data.address
            company.fiscal_year = data.fiscal_year
            company.approval_threshold = data.approval_threshold

        self.company_repo.db.commit()
        self.company_repo.db.refresh(company)

        if self.company_repo.count_accounts(company.id) == 0:
            seed_pgc(self.company_repo.db, company_id=company.id)

        return company

    def list_companies(self, current_user_id: int):
        return self.company_repo.list_by_user(current_user_id)

    def create_company(self, data: CompanyIn, current_user_id: int) -> Company:
        company = self.company_repo.create(data.model_dump())
        self.membership_repo.create(current_user_id, company.id)
        self.company_repo.db.commit()
        self.company_repo.db.refresh(company)
        return company
