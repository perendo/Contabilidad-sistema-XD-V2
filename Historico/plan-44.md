## Story
Como administrador, quiero poder rechazar una factura propuesta indicando el motivo, para corregirla o descartarla. Requiere: #41

## Acceptance criteria
- [ ] Dado una factura recibida pendiente de aprobación en la bandeja, cuando el usuario la rechaza indicando un motivo, entonces el sistema marca la factura como rechazada con ese motivo y no crea asiento contable.
- [ ] Dado una factura recibida rechazada, cuando el usuario consulta la bandeja de aprobación, entonces la factura no aparece como pendiente (quedó fuera de la bandeja).
- [ ] Dado una factura recibida rechazada, cuando el usuario consulta el detalle de la factura, entonces se muestra el motivo de rechazo registrado.

## Plan
- Persistir el motivo de rechazo en la factura pendiente y marcarla como rechazada.
- Excluir las facturas rechazadas de la bandeja de pendientes.
- Exponer el motivo de rechazo en la respuesta de consulta de facturas recibidas/pendientes.
- No crear asiento contable ni documento al rechazar.

## Out of scope
- Volver a aprobar una factura ya rechazada (queda para otra historia si se necesita).
- Edición de la factura después del rechazo (corregir y re-enviar).
- Auditoría de quién rechazó (queda para otra historia si se necesita).

## Suggestions (your call)
- Reutilizar el endpoint `POST /received-invoices/pending/{id}/reject` existente de #41, asegurando que guarde el motivo y excluya del listado de pendientes.
