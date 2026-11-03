from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .accounts import router as accounts_router
from .auth import router as auth_router
from .company import router as company_router
from .invoices import router as invoices_router
from .irpf_summary import router as irpf_summary_router
from .iva_liquidation import router as iva_liquidation_router
from .libro_registro import router as libro_registro_router
from .modelo_347 import router as modelo_347_router
from .journal_entries import router as journal_entries_router
from .received_invoices import router as received_invoices_router
from .third_parties import router as third_parties_router
from .config import settings

app = FastAPI(title="Contabilidad")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(company_router)
app.include_router(accounts_router)
app.include_router(journal_entries_router)
app.include_router(third_parties_router)
app.include_router(invoices_router)
app.include_router(iva_liquidation_router)
app.include_router(irpf_summary_router)
app.include_router(libro_registro_router)
app.include_router(modelo_347_router)
app.include_router(received_invoices_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
