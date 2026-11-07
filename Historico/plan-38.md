## Story
Como administrador, quiero que el sistema valide el proveedor, la base, el tipo de IVA, la cuota y el total extraídos y me avise de incoherencias antes de confirmar, para evitar errores fiscales.

## Acceptance criteria
- [ ] Dado un archivo de factura subido y sus datos extraídos, cuando base × tipo IVA % no coincide con la cuota IVA extraída, entonces el sistema devuelve los datos extraídos junto con un aviso de incoherencia y no crea asiento contable ni factura.
- [ ] Dado un archivo de factura subido y sus datos extraídos, cuando base + cuota IVA − retención IRPF no coincide con el total extraído, entonces el sistema devuelve los datos extraídos junto con un aviso de incoherencia y no crea asiento contable ni factura.
- [ ] Dado un archivo de factura subido, cuando no se puede identificar al proveedor (sin NIF ni nombre), entonces el sistema devuelve un aviso de proveedor no identificado y no crea asiento contable ni factura.

## Plan
- Recibir el archivo subido y extraer los datos de la factura (proveedor, número, fecha, base, tipo de IVA, cuota, total).
- Validar la coherencia aritmética entre base, tipo IVA, cuota y total, y que el proveedor esté identificado.
- Devolver los datos extraídos junto con los avisos de incoherencia encontrados, sin crear asiento ni factura.
- Solo al confirmar explícitamente el usuario (con o sin ediciones), registrar la factura y su asiento.

## Out of scope
- Umbral de importe para aprobación y registro automático por debajo del umbral (historias #39 y #40).
- Bandeja de facturas pendientes de aprobación, aprobar/rechazar con motivo (historias #41 al #44).
- Cotejo a tres vías con órdenes de compra y albaranes.

## Suggestions (your call)
- Reutilizar el endpoint de extracción existente (`/received-invoices/extract` de #37) para devolver también los avisos de coherencia, ya que esa lógica ya está implementada.
