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
11. [x] Como administrador, quiero ver el balance de sumas y saldos, para verificar la corrección contable. Requiere: #1, #2
12. [x] Como administrador, quiero ver la cuenta de pérdidas y ganancias y los extractos de cuenta por rango de fechas, para evaluar el rendimiento financiero. Requiere: #1, #2
13. [x] Como administrador, quiero exportar los informes a PDF, CSV o Excel, para compartirlos externamente. Requiere: #11, #12
14. [x] Como administrador, quiero seleccionar el ejercicio contable al entrar al sistema, para poder trabajar con dos ejercicios a la vez durante el cierre de enero. Requiere: #1
15. [x] Como administrador, quiero registrar clientes y proveedores con su NIF/CIF y vincularlos a subcuentas, para generar modelos fiscales (347, IVA, IRPF) con el tercero identificado. Requiere: #1
16. [x] Como administrador, quiero adjuntar, listar y descargar documentos en un asiento del libro diario, para respaldar la operación y facilitar auditorías. Requiere: #2
17. [x] Como administrador, quiero eliminar documentos adjuntos de un asiento, para corregir errores de carga. Requiere: #16
18. [x] Como administrador, quiero importar un Excel de movimientos bancarios y vincular su IBAN a una subcuenta del PGC, para que cada movimiento quede como asiento en borrador listo para revisar. Requiere: #2
19. [x] Como administrador, quiero aceptar un asiento borrador solo si está cuadrado y revisado, para garantizar la corrección contable. Requiere: #18
20. [x] Como administrador, quiero corregir asientos aceptados mediante un apunte de corrección, para no alterar el histórico. Requiere: #19
21. [x] Como administrador, quiero que los asientos aceptados no se puedan borrar, para preservar la trazabilidad. Requiere: #19
22. [x] Como administrador, quiero importar facturas recibidas desde documento (PDF/XML) y extraer automáticamente los datos del proveedor para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #5, #15, #16 (implementado: importación desde XML FacturaE; PDF movido a #26)
23. [x] Como administrador, quiero exportar la liquidación de IVA de un periodo a PDF, CSV o Excel, para compartir la liquidación externamente. Requiere: #13, #7 (IRPF, Modelo 347 y cuenta de pérdidas y ganancias movidos a #27, #28 y #29)
24. [x] Como administrador, quiero importar movimientos bancarios desde un fichero Norma 43 CSB asignando al IBAN su cuenta contable del PGC, para revisarlos como asientos en borrador antes de aceptarlos. Requiere: #18
25. [x] Como administrador, quiero guardar perfiles de importación por banco, para poder importar extractos con distintas columnas sin cambiar el sistema. Requiere: #18
26. [x] Como administrador, quiero importar facturas recibidas desde PDF con texto extraíble, extrayendo los datos del proveedor y de la factura para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #22
27. [x] Como administrador, quiero exportar el resumen trimestral de IRPF a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #8
28. [x] Como administrador, quiero exportar el Modelo 347 a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #9
29. [x] Como administrador, quiero exportar la cuenta de pérdidas y ganancias a PDF, CSV o Excel, para compartirla externamente. Requiere: #13, #12
30. [x] Como administrador, quiero que los datos de cada sociedad (plan de cuentas, asientos, facturas, terceros, IBANs y perfiles) estén completamente aislados, para poder gestionar varias empresas sin mezclar información. Requiere: #1
31. [x] Como administrador, quiero crear, editar y seleccionar la sociedad activa al entrar al sistema, para trabajar con una empresa a la vez. Requiere: #1, #30
32. [x] Como administrador, quiero migrar la configuración y los datos existentes a una sociedad por defecto, para no perder información al activar multisociedad. Requiere: #30, #31
33. [x] Como administrador, quiero que los documentos adjuntos y los perfiles de importación bancaria se asocien a la sociedad activa. Requiere: #30, #31
34. [x] Como administrador, quiero dar de alta otros usuarios con email y contraseña, para que cada persona acceda con su propia cuenta. Requiere: #1
35. [x] Como administrador, quiero que cada asiento manual registre el usuario que lo creó, para identificar su autor. Requiere: #1, #34
36. [x] Como administrador, quiero que los asientos generados automáticamente (facturas emitidas/recibidas, tesorería, importación bancaria y correcciones) registren al usuario que los generó, para mantener la trazabilidad. Requiere: #34, #35
37. [x] Como administrador, quiero subir una factura recibida escaneada (PDF o imagen) y revisar los datos extraídos en un formulario editable, para registrarla sin teclearla y con el documento original adjunto.
38. [x] Como administrador, quiero que el sistema valide el proveedor, la base, el tipo de IVA, la cuota y el total extraídos y me avise de incoherencias antes de confirmar, para evitar errores fiscales. Requiere: #37
39. [x] Como administrador, quiero configurar un importe umbral a partir del cual una factura requiere aprobación, para que las operaciones de alto riesgo no se registren sin revisión. Requiere: #37
40. [x] Como administrador, quiero que las facturas por debajo del umbral y sin avisos se registren automáticamente, para agilizar las facturas habituales. Requiere: #39
41. [x] Como administrador, quiero una bandeja de facturas pendientes de aprobación donde ver el documento original, los datos extraídos y el motivo de la pausa, para aprobarlas o rechazarlas. Requiere: #39
42. [x] Como administrador, quiero que al aprobar una factura se cree el asiento contable y quede registrado quién y cuándo la aprobó, para mantener la trazabilidad. Requiere: #41
43. [x] Como administrador, quiero que las aprobaciones pendientes se conserven al cerrar sesión o reiniciar el sistema, para no perder trabajo. Requiere: #41
44. [x] Como administrador, quiero poder rechazar una factura propuesta indicando el motivo, para corregirla o descartarla. Requiere: #41

45. [x] Como administrador, quiero que el sistema valide mi membresía a una empresa para que no pueda acceder a datos de otras empresas.
46. [x] Como administrador, quiero gestionar usuarios y asignar roles y sociedades para controlar quién puede acceder a cada empresa.
47. [x] Como administrador, quiero que el sistema valide contraseñas y proteja contra ataques de fuerza bruta y temporización para evitar el acceso no autorizado.
48. [x] Como administrador, quiero que los archivos subidos (PDF, imagen, XML) se procesen de forma segura para evitar ataques de inyección o descompresión.
49. [x] Como administrador, quiero que el procesamiento de facturas escaneadas se realice de forma asíncrona para no bloquear el servidor.
50. [x] Como administrador, quiero que la numeración de facturas sea correlativa y aislada por empresa para cumplir con la normativa tributaria.
51. [ ] Como desarrollador backend, quiero que las consultas a la base de datos usen joins eficientes y agregación SQL para evitar problemas de rendimiento.
52. [ ] Como administrador, quiero que los listados de datos estén paginados para evitar el colapso del servidor y del frontend.
53. [ ] Como desarrollador backend, quiero que el código esté organizado en capas separadas (rutas, servicios, repositorios) para facilitar el mantenimiento y la seguridad.
54. [ ] Como administrador, quiero que los importes contables se manejen con precisión decimal para evitar errores en informes fiscales.
55. [ ] Como desarrollador frontend, quiero que la interfaz tenga componentes reutilizables y manejo de errores adecuado para facilitar el mantenimiento.
56. [ ] Como desarrollador frontend, quiero que CORS permita el encabezado X-Company-Id para evitar errores en llamadas entre dominios.
57. [ ] Como administrador, quiero que el sistema mantenga un registro inalterable de auditoría para cumplir con la Ley Antifraude y Veri*factu. Requiere: #45.
58. [ ] Como administrador, quiero que el informe de Pérdidas y Ganancias siga la estructura del PGC español para cumplir con la normativa contable.
59. [ ] Como administrador, quiero que el extracto de cuenta muestre el saldo inicial correcto para tener una visión real de mis finanzas.
60. [ ] Como administrador, quiero que el Modelo 347 tenga desglose trimestral y excluya facturas con retención de IRPF para cumplir con la AEAT. Requiere: #45.

## Automatización de facturas con agente (nuevo epic)

Sistema contable single-tenant con varias sociedades, en español y EUR. Se añade un flujo de automatización de facturas recibidas con OCR/LLM y aprobación humana antes de registrar operaciones irreversibles.

Stack: FastAPI + Next.js + PostgreSQL existentes; se añade LangGraph para el flujo del agente y un servicio OCR/LLM (proveedor a decidir en implementación).

Decisiones costosas: single-tenant, rol único (cualquier usuario autenticado puede aprobar), solo online, español, EUR.

Fuera de alcance: cotejo a 3 vías con órdenes de compra y albaranes; sincronización con ERP externos o e-commerce; ejecución de pagos.

## Decisiones técnicas (MVP)
- Auth: JWT (python-jose) con usuario seed en tabla `users`; credenciales del seed vía `.env` (`SEED_EMAIL`, `SEED_PASSWORD`) y script `seed.py`. Login JSON en `/auth/login`, formulario OAuth2 en `/auth/token` (usado por Swagger) y `POST /auth/logout`. El token se entrega en la cookie HttpOnly `token` (SameSite=Lax por defecto, `Secure` automático sobre HTTPS o forzable con `COOKIE_SECURE`, dominio con `COOKIE_DOMAIN`, nombre configurable con `AUTH_COOKIE_NAME`) y también como bearer para clientes API. El frontend usa `credentials: "include"`, comprueba la sesión con el marcador no sensible `auth_session` y no guarda el JWT en localStorage. `POST /auth/logout` borra ambas cookies.
- Persistencia: PostgreSQL por entorno (`DATABASE_URL` / `TEST_DATABASE_URL`); migraciones con Alembic (URL desde settings).
- Tests: BD de test con `drop_all`/`create_all` por test y seed dedicado (`test@example.com` / `testpass123`). Los importes de apuntes se validan como cadenas de 2 decimales.
- Stack backend: FastAPI + SQLAlchemy 2.0 + psycopg 3.
- Stack frontend: Next.js 16 (App Router) + MUI. Panel con `NAV_ITEMS` hacia plan contable, libro diario, importación bancaria, facturas, informes y modelos fiscales; páginas en `/bank-imports`, `/reports/{balance,pyg,export}` y `/taxes/{iva,irpf,347}`. Todas validan sesión y llaman a la API con `credentials: "include"`.
- CORS: orígenes explícitos desde `CORS_ORIGINS` (por defecto `http://localhost:3000` y `http://127.0.0.1:3000`), `allow_credentials=True`, métodos GET/POST/PUT/DELETE/OPTIONS y cabeceras `Authorization`/`Content-Type`. No se usa `*` con credenciales.
- Asientos: tienen estado (draft/accepted/annulled); solo los borradores son editables/anulables. Solo se permiten apuntes en subcuentas de detalle (`is_detail == True`); se rechazan cuentas de grupo/balance. `JournalLineOut` serializa `debit`/`credit` como `Decimal` con 2 decimales (string JSON) para evitar pérdida de precisión IEEE 754.
- Terceros: tabla propia vinculada por account_id (único) a una subcuenta del plan.
- Facturas emitidas: generan un asiento aceptado en la misma transacción; cliente obligatorio de tipo `Cliente` (se adeuda su subcuenta), ventas fijas en `7000` e IVA repercutido en `4770`, tipos de IVA 21/10/4/0 y numeración correlativa por ejercicio (con `pg_advisory_xact_lock` solo si el motor es PostgreSQL). La numeración requiere sociedad activa: con `company_id` nulo el bloqueo y el índice único `(company_id, year, number)` no protegen (limitación conocida, no alcanzable con membresías). No hacer `alembic downgrade` por debajo de `d92b6a4f7e58`: borraría la tabla de facturas y dejaría huérfanos sus asientos.
- Facturas recibidas: gasto obligatorio en subcuenta de tipo `Gasto` con `is_detail`, número del proveedor obligatorio y único por proveedor (sin numeración interna), IVA 21/10/4/0 a `4720/4721/4722/4723` y asiento aceptado en la misma transacción. El seed del PGC solo se ejecuta al guardar la empresa si aún no existe ninguna cuenta contable.
- Tesorería: las facturas emitidas y recibidas tienen estado de pago (`pendiente` por defecto). Al marcar una emitida como `cobrada` o una recibida como `pagada`, se crea un asiento de tesorería aceptado por el total en la misma transacción (emitida: débito cuenta de tesorería 57, crédito cliente; recibida: débito proveedor, crédito tesorería 57). Las facturas ya pagadas/cobradas no se pueden volver a marcar.
- Liquidación de IVA: `GET /iva-liquidation?date_from=&date_to=` suma el IVA repercutido de facturas emitidas (devengado, `4770`) y el IVA soportado de facturas recibidas (deducible, `4720/4721/4722/4723`) filtrado por `date`, calcula el saldo (a ingresar / a compensar / neutro) y devuelve el desglose por tipo de IVA (21/10/4/0). Es solo lectura e idempotente; no genera asiento contable.
- Retenciones de IRPF: `Invoice` y `ReceivedInvoice` tienen campos opcionales `irpf_rate` y `irpf_amount` (porcentaje e importe retenido) para facturas de profesionales, alquileres y nóminas. Las facturas emitidas registran la retención soportada en la cuenta `4730` y las recibidas la retención practicada en `4751`. `GET /irpf-summary?year=&quarter=` devuelve el resumen trimestral separando `modelo_111` (facturas recibidas, retenciones practicadas a ingresar) y `pagos_a_cuenta_130` (facturas emitidas, retenciones soportadas), con bases, importes y número de facturas por grupo; solo lectura e idempotente; no genera asiento contable.
- Modelo 347: `GET /modelo-347?year=&threshold=` agrupa facturas emitidas y recibidas del ejercicio por tercero (NIF/CIF), suma el importe total anual de operaciones y devuelve los terceros que superan el umbral configurado; solo lectura e idempotente.
- Libros registro fiscales: `GET /libro-registro?year=` devuelve el listado detallado de facturas emitidas y recibidas del ejercicio con fecha, número/número de proveedor, NIF y nombre del tercero, base imponible, tipo IVA, cuota IVA, tipo IRPF, cuota IRPF y total, con totales por tipo de documento; solo lectura e idempotente.
- Balance de sumas y saldos: `GET /balance-sumas-saldos?date_from=&date_to=` agrupa con `SUM` en SQL los apuntes del libro diario (solo asientos aceptados) por cuenta dentro del rango de fechas, devuelve por cuenta el debe, el haber y el saldo, con totales globales y un booleano `cuadrado` (total_debe == total_haber); solo lectura e idempotente.
- Cuenta de pérdidas y ganancias: `GET /cuenta-perdidas-ganancias?date_from=&date_to=` agrega con `SUM` en SQL los apuntes de cuentas de tipo Ingreso (crédito - débito) y Gasto (débito - crédito) dentro del rango, considerando solo asientos aceptados, y devuelve total_ingresos, total_gastos, resultado y tipo (beneficio/pérdida/neutro); solo lectura e idempotente.
- Extracto de cuenta: `GET /extracto-cuenta?account_id=&date_from=&date_to=` devuelve los movimientos de una cuenta (fecha, asiento, descripción, debe, haber, saldo acumulado) con totales y saldo final, considerando solo asientos aceptados (excluye borradores y anulados); solo lectura e idempotente.
- Exportación de informes: `GET /exportar-balance?date_from=&date_to=&format=csv|pdf|xlsx` exporta el balance de sumas y saldos; `GET /exportar-iva?date_from=&date_to=&format=...` la liquidación de IVA; `GET /exportar-irpf?year=&quarter=&format=...` el resumen IRPF; `GET /exportar-modelo-347?year=&threshold=&format=...` el Modelo 347; `GET /exportar-pyg?date_from=&date_to=&format=...` la cuenta de pérdidas y ganancias. Todos a CSV/PDF/XLSX descargables, solo lectura e idempotentes.
- Documentos adjuntos: los ficheros se guardan en disco fuera de la base de datos, en `Data/<nombre-Empresa>/<año-del-asiento>/` con un nombre generado que conserva la extensión (raíz configurable con `DOCUMENTS_DIR`, por defecto `Data/` en la raíz del repositorio, ignorada por git y montada como volumen persistente en despliegues); la tabla `documents` conserva los metadatos, la ruta del fichero y el nombre original (usado en la descarga). Al eliminar un adjunto se borra también su fichero y, si un asiento en borrador cambia de ejercicio, sus documentos se mueven a la carpeta del nuevo año. Los documentos ya almacenados en la BD se migran a disco. Endpoints canónicos `POST/GET /journal-entries/{entry_id}/attachments` (subida multipart con campo `file` y listado de metadatos) y `GET/DELETE /attachments/{attachment_id}` (descarga y eliminación). Sin rutas ni alias de campos alternativos. Se valida MIME permitido (PDF, PNG, JPEG, XML), tamaño máximo 10 MB y `Content-Disposition` seguro.
- Importación bancaria: `POST /bank-imports` (multipart `file` `.xlsx` obligatorio y `account_id` opcional) detecta el IBAN en cualquier celda del Excel y localiza la cabecera por alias (`Fecha Operación`/`Fecha`, `Concepto`/`Descripción`, `Importe`/`Cantidad`). El IBAN se normaliza (mayúsculas y sin espacios) y se vincula en `bank_iban_accounts` a una subcuenta de detalle cuyo código empiece por `57`; si llega `account_id`, se reasigna y guarda el vínculo, y si el IBAN ya está vinculado se reutiliza sin pedirlo. Cada movimiento crea un asiento borrador con el banco al debe en los abonos y al haber en los cargos, usando la cuenta `555` como contrapartida. Se validan todas las filas antes de crear nada y se devuelven las filas con error; sin vista previa, detección de duplicados ni conversión de divisa.
- Aceptación de borradores: los asientos tienen un campo `reviewed` (por defecto `false`). `POST .../review` (alias `/revisar`) marca un borrador como revisado; `POST .../accept` (alias `/aceptar`) transiciona borrador → aceptado solo si `reviewed == true` y el asiento está cuadrado (revalidando cuadre y cuentas de detalle); en caso contrario devuelve 400 y el asiento permanece borrador. Solo los borradores son revisables/aceptables.
- Corrección de aceptados: los asientos tienen un campo nullable `correction_of_entry_id` (FK a `journal_entries.id`). `POST .../correct` (alias `/corregir`) valida que el original esté aceptado y crea un nuevo asiento aceptado vinculado al original, sin modificarlo; las líneas se validan como cualquier asiento (cuadre + cuentas de detalle). Se expone el vínculo como `correction_of_entry_id`/`corrects_entry_id`/`original_entry_id`.
- Borrado de asientos: `DELETE ...` (alias `/eliminar`/`/borrar`) solo borra asientos en estado `draft` (líneas y documentos, incluidos los ficheros del disco); los aceptados y anulados devuelven 400, los inexistentes 404; respuesta 204.
- Importación de facturas recibidas desde XML: `POST /received-invoices/import` (multipart) parsea FacturaE, reutiliza o crea automáticamente el tercero (con subcuenta de detalle auto-generada bajo 4000) avisando con `supplier_created`, reutiliza el flujo de factura recibida y adjunta el XML al asiento; errores de parseo/validación → 400 sin crear nada. El mismo endpoint acepta PDF con texto extraíble (pdfminer.six): extrae NIF, número, fecha, base e IVA por patrones y reutiliza la misma creación/adjunto; PDFs sin texto o sin datos → 400.
- Autoría de asientos automáticos: las facturas (incluida su importación), la tesorería, la importación bancaria y las correcciones guardan el `author_id` del usuario autenticado al generar el asiento; los asientos manuales lo guardan en el alta.
- Extracción asíncrona de facturas escaneadas: `POST /received-invoices/extract` valida el tipo de archivo, guarda el fichero y encola un trabajo en `received_invoice_jobs`, respondiendo `202` con `job_id`; el OCR, la validación y el auto-registro/pendiente se ejecutan en una tarea de fondo con sesión propia y el resultado se consulta con `GET /received-invoices/jobs/{job_id}` (aislado por sociedad).
