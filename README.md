# Contabilidad Sistema XD V2

Sistema de gestión contable (MVP) para una única empresa, en español y euro. Cubre plan de cuentas, libro diario, facturación, tesorería, liquidación de IVA/IRPF, declaraciones informativas, libros registro fiscales e informes financieros.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (psycopg 3), migraciones con Alembic.
- **Frontend:** Next.js (App Router) + Material UI.
- **Auth:** JWT bearer (python-jose) con usuario seed.

## Requisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL

## Configuración del backend

1. Crear un archivo `.env` en `backend/` (ver `.env.example` si existe) con:

```env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/contabilidad
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/contabilidad_test
SECRET_KEY=cambia-esta-clave
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SEED_EMAIL=admin@example.com
SEED_PASSWORD=adminpass
CORS_ORIGINS=http://localhost:3000
DOCUMENTS_DIR=H:/Contabilidad-sistema-XD-V2/Data
```

`DOCUMENTS_DIR` es opcional: si no se define, se usa `Data/` en la raíz del repositorio. En despliegues conviene indicar una ruta absoluta a un volumen persistente.

2. Instalar dependencias:

```bash
cd backend
pip install -r requirements.txt
```

3. Aplicar migraciones:

```bash
alembic upgrade head
```

4. (Opcional) Seed del usuario:

```bash
python seed.py
```

5. Arrancar el servidor:

```bash
uvicorn app.main:app --reload
```

API disponible en `http://localhost:8000` (docs en `/docs`).

## Configuración del frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en `http://localhost:3000`. Configurar `NEXT_PUBLIC_API_URL` si el backend no está en `http://localhost:8000`.

## Documentos adjuntos

Los adjuntos de los asientos se guardan como ficheros, fuera de la base de datos:

```
Data/
  <nombre-Empresa>/
    <año-del-asiento>/
      <nombre-generado>.<ext>
```

- En disco se usa un nombre generado; el nombre original se conserva en la base de datos para la descarga.
- `DOCUMENTS_DIR` permite cambiar la raíz (por defecto, `Data/` en la raíz del repositorio).
- `Data/` no se versiona (`.gitignore`). En contenedores debe montarse como volumen persistente.
- La copia de seguridad debe incluir la base de datos y `Data/`; por separado no permiten restaurar los adjuntos.
- `alembic upgrade head` traslada automáticamente los documentos existentes que aún estén en la base de datos y requiere permisos de escritura sobre `Data/`. El downgrade los devuelve a la base de datos sin borrar los ficheros.

## Tests

```bash
cd backend
pytest
```

Los tests usan `TEST_DATABASE_URL` y recrean el esquema en cada ejecución.

## Funcionalidades implementadas

- Autenticación por email/contraseña y configuración de empresa.
- Plan de cuentas jerárquico con búsqueda.
- Libro diario: creación de asientos equilibrados con múltiples líneas y consulta con filtro por fechas.
- Facturas emitidas con IVA (21/10/4/0), numeración correlativa por ejercicio y asiento contable generado automáticamente.
- Seed automático del Plan General Contable al configurar la empresa.

## Estructura

```
backend/   API FastAPI, modelos, migraciones y tests
frontend/  Aplicación Next.js
Data/      (local, no versionado)
Historias/ (local, no versionado)
```

## Licencia

Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0** (GPL-3.0). Consulta el archivo [LICENSE](LICENSE) para más detalles.