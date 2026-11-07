## Story
Como administrador, quiero que las facturas por debajo del umbral y sin avisos se registren automáticamente, para agilizar las facturas habituales.

## Acceptance criteria
- [ ] Dado un archivo de factura subido, cuando el total está por debajo del umbral configurado, no hay warnings de coherencia y el tercero ya existe, entonces el sistema registra la factura automáticamente (asiento aceptado y documento adjunto) sin requerir confirmación explícita del usuario.
- [ ] Dado un archivo de factura subido, cuando el total está por debajo del umbral y no hay warnings pero el tercero no existe, entonces el sistema abre el formulario de alta automática del tercero (según el flujo de Story #37) y no registra la factura hasta que se dé de alta el tercero.
- [ ] Dado un archivo de factura subido, cuando el total es igual o superior al umbral o hay warnings de coherencia, entonces el sistema devuelve los datos extraídos y warnings para revisión manual sin registrar automáticamente.
- [ ] Dado que no hay umbral configurado para la sociedad activa, cuando se sube una factura, entonces el sistema no registra automáticamente y devuelve los datos para revisión manual.

## Plan
- Recibir el archivo y extraer datos + warnings como en #37/#38.
- Obtener el umbral de aprobación de la sociedad activa.
- Verificar que el tercero (proveedor) ya exista; si no existe, abrir formulario de alta automática (Story #37) y no registrar aún.
- Si hay umbral, total por debajo del umbral, no hay warnings y el tercero existe, registrar la factura automáticamente (asiento aceptado + documento adjunto).
- Devolver indicador de registro automático y los datos de la factura creada, o los datos + warnings / formulario de alta para revisión manual si no aplica.
- Si no hay umbral configurado, mantener el comportamiento de revisión manual actual.

## Out of scope
- Bandeja de facturas pendientes de aprobación, aprobar/rechazar con motivo (historias #41 y #44).
- Trazabilidad de quién y cuándo aprobó (historia #42).
- Persistencia de aprobaciones al cerrar sesión (historia #43).
- Creación automática del tercero sin intervención del usuario cuando no existe.

## Suggestions (your call)
- Reutilizar el endpoint de extracción de #37 para devolver también un campo `auto_registered` booleano y, cuando corresponda, ejecutar internamente el flujo de confirmación sin requerir llamada separada a /confirm.
