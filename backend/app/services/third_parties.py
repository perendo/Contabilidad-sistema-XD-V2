from ..repositories.third_parties import ThirdPartyRepository
from ..schemas.third_parties import ALLOWED_TYPES, _normalize_type


class ThirdPartyService:
    def __init__(self, repo: ThirdPartyRepository):
        self.repo = repo

    def create_third_party(self, data, company_id) -> dict:
        if data.type not in ALLOWED_TYPES:
            raise ValueError("Tipo de tercero no válido")
        account = self.repo.get_account(data.account_id, company_id)
        if account is None:
            raise ValueError("Subcuenta no existe")
        normalized = _normalize_type(data.type)
        tp = self.repo.create(
            {
                "account_id": data.account_id,
                "name": data.name,
                "tax_id": data.tax_id,
                "type": normalized,
                "address": data.address,
                "phone": data.phone,
                "email": data.email,
            },
            company_id,
        )
        self.repo.commit()
        self.repo.refresh(tp)
        return tp

    def list_third_parties(self, company_id, type=None, search=None):
        return self.repo.list_by_company(company_id, type, search)
