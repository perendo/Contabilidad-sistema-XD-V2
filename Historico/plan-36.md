## Historia
Como administrador, quiero que los asientos generados automáticamente (facturas emitidas/recibidas, tesorería, importación bancaria y correcciones) registren al usuario que los generó, para mantener la trazabilidad.

## Criterios de aceptación
- [ ] Dado un usuario autenticado, cuando registra una factura emitida o recibida, o la marca como cobrada/pagada, entonces el asiento generado registra a ese usuario como autor.
- [ ] Dado un usuario autenticado, cuando importa movimientos bancarios, entonces los asientos creados registran a ese usuario como autor.
- [ ] Dado un usuario autenticado, cuando corrige un asiento aceptado, entonces el asiento de corrección registra a ese usuario como autor.

## Plan
- Añadir el autor al alta común de asientos automáticos.
- Registrar el autor en facturas emitidas/recibidas y en sus asientos de cobro/pago.
- Registrar el autor también al importar facturas recibidas desde PDF/XML.
- Registrar el autor en la importación bancaria (asientos en borrador) y en las correcciones.
- Comprobar que el libro diario muestra el autor sin cambios adicionales.

## Fuera de alcance
- Cambios de esquema o migraciones: el campo de autor ya existe desde #35.
- Autoría de asientos manuales (#35, ya completada).
- Editar el autor de asientos existentes.
- Registrar quién revisa, acepta o anula un asiento.

## Sugerencias (tu decisión)
- Ninguna.
