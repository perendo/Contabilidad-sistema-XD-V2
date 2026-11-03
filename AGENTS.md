# Backlog

## Contexto
Sistema de gestión contable (MVP) para una única empresa, en español y euro, con autenticación por email y contraseña. Cubre plan de cuentas, libro diario, facturación, tesorería, liquidación de IVA/IRPF, declaraciones informativas, libros registro fiscales e informes financieros.

Stack: FastAPI + Next.js + PostgreSQL

Decisiones costosas: single-tenant, rol único (email/contraseña), solo online, idioma único (español) y moneda única (EUR).

## Backlog

1. [x] Como administrador, quiero iniciar sesión con mi email y contraseña y configurar los datos básicos de mi empresa y el plan de cuentas, para poder empezar a usar el sistema.
2. [x] Como administrador, quiero crear asientos contables equilibrados con múltiples líneas, para registrar transacciones económicas siguiendo la partida doble.
3. [x] Como administrador, quiero editar o anular asientos no consolidados, para corregir errores. Requiere: #2
4. [x] Como administrador, quiero registrar facturas emitidas (ventas) con IVA, para que el sistema genere automáticamente el asiento contable.
5. [x] Como administrador, quiero registrar facturas recibidas (compras/gastos) con IVA, para que el sistema genere automáticamente el asiento contable.
6. [x] Como administrador, quiero marcar facturas como pendientes, pagadas o cobradas y generar asientos de tesorería, para controlar el flujo de caja. Requiere: #4, #5
7. [x] Como administrador, quiero liquidar el IVA de un periodo (devengado vs. deducible) con saldos a compensar, para cumplir con las obligaciones fiscales. Requiere: #4, #5
8. [x] Como administrador, quiero gestionar retenciones de IRPF en facturas de profesionales, alquileres y nóminas, para preparar resúmenes trimestrales. Requiere: #4, #5
9. [x] Como administrador, quiero identificar terceros que superen el umbral de operaciones, para preparar declaraciones informativas (Modelo 347). Requiere: #4, #5
10. [x] Como administrador, quiero generar los libros registro fiscales de facturas emitidas y recibidas, para presentarlos ante la administración. Requiere: #4, #5
11. [ ] Como administrador, quiero ver el balance de sumas y saldos, para verificar la corrección contable. Requiere: #1, #2
12. [ ] Como administrador, quiero ver la cuenta de pérdidas y ganancias y los extractos de cuenta por rango de fechas, para evaluar el rendimiento financiero. Requiere: #1, #2
13. [ ] Como administrador, quiero exportar los informes a PDF, CSV o Excel, para compartirlos externamente. Requiere: #11, #12
14. [ ] Como administrador, quiero seleccionar el ejercicio contable al entrar al sistema, para poder trabajar con dos ejercicios a la vez durante el cierre de enero. Requiere: #1
15. [x] Como administrador, quiero registrar clientes y proveedores con su NIF/CIF y vincularlos a subcuentas, para generar modelos fiscales (347, IVA, IRPF) con el tercero identificado. Requiere: #1
16. [ ] Como administrador, quiero adjuntar, listar y descargar documentos en un asiento del libro diario, para respaldar la operación y facilitar auditorías. Requiere: #2
17. [ ] Como administrador, quiero eliminar documentos adjuntos de un asiento, para corregir errores de carga. Requiere: #16
18. [ ] Como administrador, quiero registrar asientos en borrador pendientes de validación, para poder introducir movimientos bancarios importados y revisarlos antes de aceptarlos. Requiere: #2
19. [ ] Como administrador, quiero aceptar un asiento borrador solo si está cuadrado y revisado, para garantizar la corrección contable. Requiere: #18
20. [ ] Como administrador, quiero corregir asientos aceptados mediante un apunte de corrección, para no alterar el histórico. Requiere: #19
21. [ ] Como administrador, quiero que los asientos aceptados no se puedan borrar, para preservar la trazabilidad. Requiere: #19
22. [ ] Como administrador, quiero importar facturas recibidas desde documento (PDF/XML) y extraer automáticamente los datos del proveedor para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #5, #15, #16

## Decisiones técnicas (MVP)
- Auth: JWT bearer (python-jose) con usuario seed en tabla `users`; credenciales del seed vía `.env` (`SEED_EMAIL`, `SEED_PASSWORD`) y script `seed.py`. Login JSON en `/auth/login` y formulario OAuth2 en `/auth/token` (usado por Swagger).
- Persistencia: PostgreSQL por entorno (`DATABASE_URL` / `TEST_DATABASE_URL`); migraciones con Alembic (URL desde settings).
- Tests: BD de test con `drop_all`/`create_all` por test y seed dedicado (`test@example.com` / `testpass123`).
- Stack backend: FastAPI + SQLAlchemy 2.0 + psycopg 3; frontend Next.js pendiente.
- Asientos: tienen estado (draft/accepted/annulled); solo los borradores son editables/anulables.
- Terceros: tabla propia vinculada por account_id (único) a una subcuenta del plan.
- Facturas emitidas: generan un asiento aceptado en la misma transacción; cliente obligatorio de tipo `Cliente` (se adeuda su subcuenta), ventas fijas en `7000` e IVA repercutido en `4770`, tipos de IVA 21/10/4/0 y numeración correlativa por ejercicio. No hacer `alembic downgrade` por debajo de `d92b6a4f7e58`: borraría la tabla de facturas y dejaría huérfanos sus asientos.
- Facturas recibidas: gasto obligatorio en subcuenta de tipo `Gasto` con `is_detail`, número del proveedor obligatorio y único por proveedor (sin numeración interna), IVA 21/10/4/0 a `4720/4721/4722/4723` y asiento aceptado en la misma transacción. El seed del PGC se ejecuta en cada guardado de empresa y es idempotente.
- Tesorería: las facturas emitidas y recibidas tienen estado de pago (`pendiente` por defecto). Al marcar una emitida como `cobrada` o una recibida como `pagada`, se crea un asiento de tesorería aceptado por el total en la misma transacción (emitida: débito cuenta de tesorería 57, crédito cliente; recibida: débito proveedor, crédito tesorería 57). Las facturas ya pagadas/cobradas no se pueden volver a marcar.
- Liquidación de IVA: `GET /iva-liquidation?date_from=&date_to=` suma el IVA repercutido de facturas emitidas (devengado, `4770`) y el IVA soportado de facturas recibidas (deducible, `4720/4721/4722/4723`) filtrado por `date`, calcula el saldo (a ingresar / a compensar / neutro) y devuelve el desglose por tipo de IVA (21/10/4/0). Es solo lectura e idempotente; no genera asiento contable.
- Retenciones de IRPF: `Invoice` y `ReceivedInvoice` tienen campos opcionales `irpf_rate` y `irpf_amount` (porcentaje e importe retenido) para facturas de profesionales, alquileres y nóminas. `GET /irpf-summary?year=&quarter=` devuelve el resumen trimestral con base sujeta total, tipo de retención e importe retenido total; solo lectura e idempotente; no genera asiento contable.
- Modelo 347: `GET /modelo-347?year=&threshold=` agrupa facturas emitidas y recibidas del ejercicio por tercero (NIF/CIF), suma el importe total anual de operaciones y devuelve los terceros que superan el umbral configurado; solo lectura e idempotente.
- Libros registro fiscales: `GET /libro-registro?year=` devuelve el listado detallado de facturas emitidas y recibidas del ejercicio con fecha, número/número de proveedor, NIF y nombre del tercero, base imponible, tipo IVA, cuota IVA, tipo IRPF, cuota IRPF y total, con totales por tipo de documento; solo lectura e idempotente.
