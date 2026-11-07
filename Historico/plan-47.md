## Story
Como administrador, quiero que los archivos subidos (PDF, imagen, XML) se procesen de forma segura para evitar ataques de inyección o descompresión.

## Acceptance criteria
- [ ] Dado un archivo PDF con bomba de descompresión, cuando se sube, entonces el sistema devuelve 400 sin procesar el archivo.
- [ ] Dada una imagen con bomba de descompresión (bombas de píxeles), cuando se sube, entonces el sistema devuelve 400 sin procesar la imagen.
- [ ] Dado un archivo XML FacturaE con entidades externas (XXE), cuando se sube, entonces el sistema devuelve 400 sin procesar entidades externas.

## Plan
- Agregar límite de dimensiones (píxeles) en imágenes antes de procesar con PIL para evitar decompression bombs.
- Reemplazar `xml.etree.ElementTree.fromstring` por `defusedxml.parse` para parsear FacturaE de forma segura.
- Agregar límite de tamaño de archivo PDF antes de procesar con pdfminer para evitar decompression bombs.

## Out of scope
- Sincronización de perfiles de importación bancaria entre sociedades (historia #25 ya cubre perfiles).
- Cotejo a tres vías con órdenes de compra y albaranes (fuera de alcance del epic).

## Suggestions (your call)
- Reutilizar `pydantic-settings` para configurar los límites de tamaño de imagen y PDF como variables de entorno (`MAX_IMAGE_PIXELS`, `MAX_PDF_PAGES`), ya que ya está disponible como dependencia.
