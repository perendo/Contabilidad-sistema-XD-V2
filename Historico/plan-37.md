## Story
Como administrador, quiero subir una factura recibida escaneada (PDF o imagen) y revisar los datos extraídos en un formulario editable, para registrarla sin teclearla y con el documento original adjunto.

## Acceptance criteria
- [ ] Dado un usuario autenticado, cuando sube una factura recibida escaneada (PDF o imagen), entonces el sistema devuelve los datos extraídos (proveedor, número de factura, fecha, base, tipo de IVA y total) listos para revisar sin crear ningún asiento contable.
- [ ] Dados los datos extraídos presentados para revisar, cuando el usuario los edita y los confirma, entonces el sistema crea la factura recibida con su asiento contable aceptado y adjunta el documento original a ese asiento.
- [ ] Dado un archivo que no se puede leer o no contiene datos de factura, cuando el usuario lo sube, entonces el sistema devuelve un error y no persiste nada.

## Plan
- Autenticar al usuario y aceptar el archivo PDF o imagen subido.
- Extraer los datos de la factura (proveedor, número, fecha, base, tipo de IVA, total) mediante OCR/LLM.
- Devolver los datos extraídos en un payload editable para revisión; guardar el archivo original temporalmente sin crear asiento contable.
- Al confirmar el usuario (con posibles ediciones), validar y crear la factura recibida con su asiento aceptado y el autor.
- Adjuntar el documento original al nuevo asiento y devolver la factura registrada.

## Out of scope
- Validación de coherencia entre proveedor, base, tipo de IVA, cuota y total con avisos previos a confirmar (historia #38).
- Umbral de importe para aprobación y registro automático por debajo del umbral (historias #39 y #40).
- Bandeja de facturas pendientes de aprobación, aprobar/rechazar con motivo y trazabilidad de quién y cuándo (historias #41 al #44).
- Cotejo a tres vías con órdenes de compra y albaranes; sincronización con ERP o e-commerce; ejecución de pagos.

## Suggestions (your call)
- Reutilizar el flujo existente de extracción y adjunto de documentos de la importación de facturas recibidas, insertando un paso de revisión entre la extracción y el registro, ya que esa lógica ya está implementada.
