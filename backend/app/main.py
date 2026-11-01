from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .accounts import router as accounts_router
from .auth import router as auth_router
from .company import router as company_router
from .journal_entries import router as journal_entries_router
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
