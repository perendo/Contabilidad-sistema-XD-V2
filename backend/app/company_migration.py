from datetime import date

from sqlalchemy.orm import Session

from .models import (
    Account,
    BankIbanAccount,
    BankImportProfile,
    Company,
    Invoice,
    JournalEntry,
    ReceivedInvoice,
    ThirdParty,
)


DATA_MODELS = (
    Account,
    JournalEntry,
    ThirdParty,
    Invoice,
    ReceivedInvoice,
    BankIbanAccount,
    BankImportProfile,
)


def migrate_existing_to_default_company(db: Session) -> int:
    """Garantiza una sociedad por defecto y rellena company_id donde esté vacío."""
    company = db.query(Company).order_by(Company.id).first()
    if company is None:
        company = Company(
            name="Empresa por defecto",
            tax_id="B00000000",
            address="",
            fiscal_year=str(date.today().year),
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    default_id = company.id
    for model in DATA_MODELS:
        db.query(model).filter(model.company_id.is_(None)).update(
            {model.company_id: default_id}, synchronize_session=False
        )
    db.commit()
    return default_id
