## Historia
Como administrador, quiero importar facturas recibidas desde PDF con texto extraíble, extrayendo los datos del proveedor y de la factura para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #22

## Criterios de aceptación
- [ ] Dado un PDF con texto extraíble que contiene el NIF del proveedor, número de factura, fecha, base imponible e IVA, cuando lo importo, entonces se crea la factura recibida (reutilizando el proveedor si su NIF ya existe, o creándolo automáticamente si no), se genera y acepta su asiento contable y se adjunta el PDF al asiento.
- [ ] Dado un PDF del que no se pueden extraer los datos requeridos (NIF, número, fecha, base/IVA), cuando lo importo, entonces la petición se rechaza (400) con detalle y no se crea nada.
- [ ] Dado un PDF sin texto extraíble (por ejemplo, escaneado), cuando lo importo, entonces la petición se rechaza (400) indicando que no se pudo extraer texto.

## Plan
- Añadir `pdfminer.six` como dependencia y un paso de extracción de texto del PDF.
- Detectar el PDF por content-type/extensión en el endpoint de importación y enrutarlo a un extractor basado en regex para NIF, número, fecha, base e IVA.
- Reutilizar la misma canalización de proveedor/factura/asiento/adjunto que la importación XML (helper compartido).
- Rechazar con 400 ante cualquier fallo de extracción o validación, sin crear nada.

## Fuera de alcance
- OCR para PDFs escaneados o de imagen.
- Plantillas o regex personalizables por proveedor.
- Otros formatos binarios (imágenes, Word).
- Edición de los datos extraídos antes de confirmar.

## Sugerencias (opcional)
- Refactorizar la importación XML en un helper compartido `_create_from_extracted(data, file, ...)` para que la ruta PDF solo añada un extractor y ambas formatos se mantengan consistentes.
- Mantener los patrones regex permisivos (NIF/CIF con o sin espacios, fechas en formatos españoles comunes) y documentar los patrones esperados.