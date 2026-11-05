from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .accounts import router as accounts_router
from .cuenta_perdidas_ganancias import router as cuenta_perdidas_ganancias_router
from .documents import router as documents_router
from .extracto_cuenta import router as extracto_cuenta_router
from .auth import router as auth_router
from .company import router as company_router
from .invoices import router as invoices_router
from .irpf_summary import router as irpf_summary_router
from .iva_liquidation import router as iva_liquidation_router
from .libro_registro import router as libro_registro_router
from .balance_sumas_saldos import router as balance_sumas_saldos_router
from .bank_imports import router as bank_imports_router
from .exportar_balance import router as exportar_balance_router
from .exportar_iva import router as exportar_iva_router
from .exportar_irpf import router as exportar_irpf_router
from .exportar_modelo_347 import router as exportar_modelo_347_router
from .exportar_pyg import router as exportar_pyg_router
from .modelo_347 import router as modelo_347_router
from .journal_entries import router as journal_entries_router
from .received_invoices import router as received_invoices_router
from .third_parties import router as third_parties_router
from .config import settings

app = FastAPI(title="Contabilidad")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not origins or origins == ["*"]:
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(company_router)
app.include_router(accounts_router)
app.include_router(cuenta_perdidas_ganancias_router)
app.include_router(extracto_cuenta_router)
app.include_router(journal_entries_router)
app.include_router(third_parties_router)
app.include_router(invoices_router)
app.include_router(iva_liquidation_router)
app.include_router(irpf_summary_router)
app.include_router(libro_registro_router)
app.include_router(balance_sumas_saldos_router)
app.include_router(bank_imports_router)
app.include_router(exportar_balance_router)
app.include_router(exportar_iva_router)
app.include_router(exportar_irpf_router)
app.include_router(exportar_modelo_347_router)
app.include_router(exportar_pyg_router)
app.include_router(modelo_347_router)
app.include_router(received_invoices_router)
app.include_router(documents_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
