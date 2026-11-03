## Historia
Como administrador, quiero marcar facturas como pendientes, pagadas o cobradas y generar asientos de tesorería, para controlar el flujo de caja.

## Criterios de aceptación
- [ ] Dada una factura emitida en estado "pendiente", cuando el administrador la marca como "cobrada", entonces la factura muestra estado "cobrada" y se registra un movimiento de tesorería por su total.
- [ ] Dada una factura recibida en estado "pendiente", cuando el administrador la marca como "pagada", entonces la factura muestra estado "pagada" y se registra un movimiento de tesorería por su total.
- [ ] Dada una factura ya "pagada" o "cobrada", cuando el administrador intenta marcarla de nuevo, entonces la petición se rechaza y el estado permanece sin cambios.

## Plan
- Añadir un campo de estado de pago (pendiente / pagada / cobrada) a las facturas emitidas y recibidas, con valor por defecto pendiente.
- Añadir un endpoint para cambiar el estado de una factura a pagada o cobrada.
- Cuando el estado pasa a pagada o cobrada, crear un asiento de diario de tesorería aceptado por el total de la factura en la misma transacción.
- Rechazar los intentos de volver a marcar una factura ya pagada o cobrada.
- Exponer el estado en las respuestas de lista y detalle de facturas.

## Fuera de alcance
- Pagos parciales, múltiples fechas de pago o vincular asientos de tesorería a movimientos bancarios específicos.
- Editar o eliminar los asientos de tesorería generados.
- Exportar movimientos de tesorería a PDF, CSV o Excel.

## Sugerencias (opcional)
- (ninguna)
