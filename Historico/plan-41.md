## Story
Como administrador, quiero una bandeja de facturas pendientes de aprobación donde ver el documento original, los datos extraídos y el motivo de la pausa, para aprobarlas o rechazarlas.

## Acceptance criteria
- [ ] Dado que se subió una factura y no se registró automáticamente, cuando el usuario consulta la bandeja de aprobación, entonces ve la factura con sus datos extraídos (proveedor, número, fecha, base, tipo IVA, total), el motivo de la pausa y el documento original disponible.
- [ ] Dado una factura en la bandeja de aprobación, cuando el usuario la aprueba, entonces el sistema crea la factura recibida con su asiento contable aceptado y el documento original adjunto, y la factura deja de aparecer en la bandeja.
- [ ] Dado una factura en la bandeja de aprobación, cuando el usuario la rechaza indicando un motivo, entonces el sistema registra el motivo de rechazo, no crea asiento contable y la factura queda marcada como rechazada.

## Plan
- Persistir las facturas extraídas no registradas automáticamente con estado "pendiente de aprobación", motivo de pausa y referencia al archivo original.
- Endpoint GET para listar la bandeja de facturas pendientes de aprobación con datos y motivo.
- Endpoint para obtener el documento original de una factura pendiente.
- Endpoint POST para aprobar una factura pendiente: crear ReceivedInvoice + asiento aceptado + adjuntar documento original.
- Endpoint POST para rechazar una factura pendiente: registrar motivo y marcar como rechazada.

## Out of scope
- Quién y cuándo aprobó (historia #42).
- Persistencia de aprobaciones entre sesiones (historia #43).
- Facturas pendientes de pago/cobro (estado diferente).

## Suggestions (your call)
- Reutilizar el modelo Document existente para almacenar el archivo original de la factura pendiente.
