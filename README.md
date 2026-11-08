# Contabilidad Sistema XD V2

Sistema de gestión contable (MVP) en español y euro. Soporta multisociedad (varias empresas con datos aislados) y multiusuario. Cubre plan de cuentas, libro diario, facturación, tesorería, liquidación de IVA/IRPF, declaraciones informativas, libros registro fiscales e informes financieros.

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

Frontend (Vitest + Testing Library):

```bash
cd frontend
npm test
```

## Auditoría

El proyecto ha superado una re-auditoría externa independiente (Gemini, noviembre 2026) con un dictamen de **94/100 — SOBRESALIENTE** (frente a 71/100 en la primera revisión). El informe completo está en [`Historico/AUDITORIA-Contabilidad-Sistema-XD-V2.md`](Historico/AUDITORIA-Contabilidad-Sistema-XD-V2.md).

| Área | Nota |
| --- | --- |
| Lógica contable y AEAT | 96/100 |
| Seguridad y autenticación | 94/100 |
| Base de datos y rendimiento | 92/100 |
| Arquitectura backend | 93/100 |
| Frontend Next.js | 91/100 |
| Testing y cobertura | 98/100 |

Hitos verificados por la auditoría: separación de IRPF por modelo (111 y 130), total de factura con deducción de IRPF (4730/4751), informes que solo consideran asientos aceptados, documentos en disco con límite de tamaño y validación MIME, agregación en SQL, frontend completo con componentes reutilizables, aislamiento multisociedad, saneado de fórmulas en exportaciones, protección frente a ataques de temporización y registro de auditoría inmutable.

## Funcionalidades implementadas

- Autenticación por email/contraseña (usuario seed) y configuración de empresa.
- **Multisociedad:** varias empresas con datos aislados (plan de cuentas, asientos, facturas, terceros, IBANs y perfiles), con selección de sociedad activa por cabecera `X-Company-Id` (o cookie).
- Plan de cuentas jerárquico con búsqueda y creación de subcuentas.
- Libro diario: creación de asientos equilibrados con múltiples líneas, edición/anulación de borradores, revisión y aceptación, corrección de aceptados y borrado solo de borradores.
- Documentos adjuntos en asientos (subida, listado, descarga y eliminación).
- Facturas emitidas con IVA (21/10/4/0), numeración correlativa por ejercicio y asiento contable generado automáticamente; estados de pago y asiento de tesorería.
- Facturas recibidas con IVA, importación desde XML (FacturaE) y PDF con texto extraíble, y asiento contable generado automáticamente.
- Tesorería: marcado de facturas como pagadas/cobradas con asiento de cobro/pago.
- Liquidación de IVA por periodo (devengado vs. deducible) con desglose por tipo.
- Retenciones de IRPF en facturas de profesionales/alquileres/nóminas y resumen trimestral.
- Modelo 347: identificación de terceros que superan el umbral de operaciones.
- Libros registro fiscales de facturas emitidas y recibidas.
- Balance de sumas y saldos, cuenta de pérdidas y ganancias y extracto de cuenta por rango de fechas.
- Exportación de informes a CSV, PDF y Excel (balance, IVA, IRPF, Modelo 347, P&G).
- Importación bancaria desde Excel y Norma 43 (CSB): detección de IBAN, vinculación a subcuenta del PGC, creación de asientos en borrador con cuenta 555, perfiles de importación por IBAN para columnas personalizadas.
- Terceros (clientes/proveedores) con NIF/CIF vinculados a subcuentas.
- Seed automático del Plan General Contable al configurar la empresa.

## Estructura

```
backend/   API FastAPI, modelos, migraciones y tests
frontend/  Aplicación Next.js
Data/      (local, no versionado)
Historico/ (planes de historia e informes de auditoría)
```

## Licencia

Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0** (GPL-3.0). Consulta el archivo [LICENSE](LICENSE) para más detalles.