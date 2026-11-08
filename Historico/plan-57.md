## Story
Como administrador, quiero que el sistema mantenga un registro inalterable de auditoría para cumplir con la Ley Antifraude y Veri*factu.

## Acceptance criteria
- [ ] Dado que un usuario realiza una acción trazable (crear, editar, anular o aceptar un asiento; generar o aprobar una factura; marcar una factura como pagada/cobrada), cuando la acción se confirma, entonces el sistema registra de forma inalterable quién, qué, cuándo y sobre qué registro se actuó.
- [ ] Dado que existe un registro de auditoría, cuando un usuario con permisos lo consulta, entonces puede ver el historial completo de acciones con su autor, fecha y detalle, sin poder modificar ni eliminar registros existentes.
- [ ] Dado que el sistema genera el registro de auditoría, cuando se intenta alterar un registro ya grabado, entonces el sistema lo rechaza y conserva el original intacto.

## Plan
- Definir qué acciones del sistema son trazables y qué información debe quedar registrada para cada una.
- Almacenar cada acción trazable en un registro que no pueda ser editado ni borrado una vez grabado.
- Exponer una consulta de auditoría que muestre el historial completo con autor, fecha y detalle de la acción.
- Impedir la modificación o eliminación de registros de auditoría existentes.
- Vincular cada registro de auditoría a la sociedad activa para mantener el aislamiento entre empresas.

## Out of scope
- Firma digital o sellado de tiempo externo (timestamp authority).
- Exportación del registro de auditoría a formatos externos.
- Alertas o notificaciones automáticas basadas en el registro de auditoría.
- Cambios en el modelo de usuarios o roles (ya cubierto por #45).

## Suggestions (your call)
- Tabla de auditoría aparte de las tablas transaccionales, para no acoplar el historial al ciclo de vida de los datos originales.
- Campo de versión o hash por registro para detectar alteraciones posteriores sin depender de infraestructura externa.
