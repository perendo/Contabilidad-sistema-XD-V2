## Historia
Como administrador, quiero registrar facturas emitidas (ventas) con IVA, para que el sistema genere automáticamente el asiento contable.

## Criterios de aceptación
- [ ] Given un administrador autenticado y un cliente registrado, when registra una factura emitida con fecha, cliente, concepto, base y tipo de IVA (21/10/4/0), then la factura se guarda con número correlativo automático del ejercicio y queda listada mostrando número, fecha, cliente, base, cuota de IVA y total.
- [ ] Given una factura emitida guardada, when se consulta el libro diario, then aparece un asiento aceptado y cuadrado con el total en el debe de la subcuenta del cliente y, en el haber, la base en ventas y la cuota en IVA repercutido.
- [ ] Given un cliente inexistente o de tipo proveedor, una base no positiva o un tipo de IVA no permitido, when se intenta registrar la factura, then el sistema la rechaza con error sin crear factura ni asiento.

## Plan
- Modelar la factura emitida con número, ejercicio, fecha, cliente, concepto, base, tipo de IVA, cuota, total y referencia a su asiento.
- Calcular el número secuencial por ejercicio al guardar; derivar cuota y total de la base y el tipo.
- Validar cliente existente y de tipo cliente, base positiva y tipo de IVA permitido antes de persistir.
- Crear en la misma operación el asiento aceptado: debe en la subcuenta del cliente, haber en ventas y en IVA repercutido.
- Exponer alta y consulta autenticadas y añadir la página de facturas emitidas con formulario y listado.

## Fuera de alcance
- Facturas recibidas (historia #5) y su asiento.
- Estado de cobro, pagos y asientos de tesorería (historia #6).
- Retenciones de IRPF (historia #8) y libros registro fiscales (historia #10).
- Facturas rectificativas, abonos y anulación/edición de facturas ya emitidas.
- Varios tipos de IVA en una misma factura, recargo de equivalencia, descuentos y operaciones intracomunitarias o exentas.
- Series de facturación distintas de la única anual, exportación a PDF y envío al cliente.

## Sugerencias
- Reutilizar la validación y creación de asientos ya existentes en el libro diario en vez de duplicar las reglas de equilibrio (ya hay una función de validación centralizada en `backend/app/journal_entries.py`).
- Añadir restricción única por (ejercicio, número) en facturas, para que dos altas simultáneas no generen el mismo número.
- Guardar en la factura el identificador del asiento generado: la historia #6 (cobros) lo necesitará para conciliar sin volver a buscarlo.
