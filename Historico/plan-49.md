## Story
Como administrador, quiero que el procesamiento de facturas escaneadas se realice de forma asíncrona para no bloquear el servidor.

## Acceptance criteria
- [ ] Dado un PDF o imagen de factura, cuando se sube a `POST /received-invoices/extract`, entonces el sistema responde `202` con un `job_id` sin esperar al OCR.
- [ ] Dado un `job_id`, cuando se consulta `GET /received-invoices/jobs/{job_id}`, entonces devuelve el estado (`procesando`/`completado`/`fallido`) y, si terminó, los datos extraídos y el resultado del registro (auto-registrada, pendiente o error).
- [ ] Dadas dos sociedades, cuando un usuario consulta un trabajo de otra sociedad, entonces el sistema devuelve `404`.

## Plan
- Añadir la tabla `received_invoice_jobs` (trabajo, sociedad, usuario, estado, fichero, resultado y error) con su migración Alembic.
- En `POST /received-invoices/extract`, validar el tipo de fichero, guardarlo y encolar el trabajo, devolviendo `202` con el `job_id`.
- Ejecutar la extracción, validación y registro actuales en una tarea de fondo con sesión de base de datos propia.
- Añadir `GET /received-invoices/jobs/{job_id}` con aislamiento por sociedad.
- Adaptar los tests existentes de `extract` con un helper que espera al trabajo y añadir tests de encolado, consulta, error y aislamiento.

## Out of scope
- Cola distribuida (Celery/RQ), reintentos y workers externos.
- Cambios en la interfaz: todavía no existe pantalla de escaneo de facturas.
- Purga programada de trabajos y ficheros antiguos.

## Suggestions (your call)
- Reutilizar el patrón de estados en español ya usado en `received_invoice_pending` (`pendiente`, `procesando`, `completado`, `fallido`).
