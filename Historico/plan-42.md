## Story
Como administrador, quiero que al aprobar una factura se cree el asiento contable y quede registrado quién y cuándo la aprobó, para mantener la trazabilidad. Requiere: #41

## Acceptance criteria
- [ ] Dado una factura recibida pendiente de aprobación, cuando el usuario la aprueba, entonces el sistema crea el asiento contable aceptado y registra en la factura quién la aprobó (usuario) y cuándo (fecha y hora).
- [ ] Dado una factura recibida ya aprobada, cuando se consulta la factura, entonces se muestra quién y cuándo la aprobó.
- [ ] Dado una factura recibida sin aprobar, cuando se consulta la factura, entonces los campos de aprobación están vacíos.

## Plan
- Agregar campos de usuario y fecha de aprobación al modelo de factura recibida.
- Al aprobar una factura pendiente, grabar el usuario autenticado y la fecha/hora actual en esos campos.
- Exponer los campos de aprobación en la respuesta de consulta de facturas recibidas y en la respuesta de aprobación.
- No alterar el comportamiento de creación del asiento ni de rechazo.

## Out of scope
- Quién rechazó y cuándo rechazó (queda para otra historia si se necesita).
- Auditoría de otras operaciones (edición, anulación) fuera de las facturas recibidas.

## Suggestions (your call)
- Reutilizar el patrón de `author_id` ya usado en `JournalEntry` para el campo de usuario que aprobó.
