## Story
Como administrador, quiero que los archivos subidos (PDF, imagen, XML) se procesen de forma segura para evitar ataques de inyección o descompresión.

## Acceptance criteria
- [ ] Dado un PDF con bomba de descompresión (muchas páginas o muchos objetos anidados), cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura.
- [ ] Dada una imagen con dimensiones extremadamente grandes (bomba de píxeles), cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura.
- [ ] Dado un archivo XML FacturaE con entidades externas (XXE), cuando se sube, entonces el sistema devuelve 400 sin crear ningún asiento ni factura.

## Plan
- Agregar límite de tamaño de archivo (tamaño en bytes) al subir PDF o imagen, rechazando archivos que excedan el límite permitido.
- Agregar límite de dimensiones (ancho y alto en píxeles) en imágenes antes de procesar con PIL para evitar decompression bombs.
- Reemplazar `xml.etree.ElementTree.fromstring` por `defusedxml.parse` para parsear FacturaE de forma segura y evitar ataques XXE.

## Out of scope
- Validación de contenido semántico de la factura (ya cubierta por historias #37 y #38).
- Sincronización de perfiles de importación bancaria entre sociedades.
- Cotejo a tres vías con órdenes de compra y albaranes.

## Suggestions (your call)
- Reutilizar `pydantic-settings` para configurar los límites de tamaño de imagen y PDF como variables de entorno (`MAX_IMAGE_PIXELS`, `MAX_PDF_SIZE`), ya que ya está disponible como dependencia.
- Usar `defusedxml` también para cualquier otro parseo de XML en el sistema si existe.
