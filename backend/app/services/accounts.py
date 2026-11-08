from ..models import Account
from ..repositories.accounts import AccountRepository
from ..schemas.accounts import ACCOUNT_TYPES, AccountIn


class AccountService:
    def __init__(self, repo: AccountRepository):
        self.repo = repo

    def create_account(self, data: AccountIn, company_id) -> Account:
        if data.type not in ACCOUNT_TYPES:
            raise ValueError("Tipo de cuenta no válido")
        if data.parent_id is None:
            if data.level != 1:
                raise ValueError("Las cuentas de nivel 1 no tienen padre")
        else:
            parent = self.repo.get(data.parent_id)
            if parent is None or parent.company_id != company_id:
                raise ValueError("Cuenta padre no existe")
            if data.level != parent.level + 1:
                raise ValueError("El nivel debe ser nivel del padre + 1")
            if not data.code.startswith(parent.code):
                raise ValueError("El código debe comenzar por el código del padre")
            if data.level > 8:
                raise ValueError("Nivel máximo 8")
        account = self.repo.create(data.model_dump(), company_id)
        self.repo.commit()
        self.repo.refresh(account)
        return account

    def list_accounts(
        self,
        company_id,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return self.repo.list_by_company(company_id, search, limit, offset)
