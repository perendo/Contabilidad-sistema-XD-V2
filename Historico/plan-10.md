## Historia
Como administrador, quiero generar los libros registro fiscales de facturas emitidas y recibidas, para presentarlos ante la administración. Requiere: #4, #5

## Criterios de aceptación
- [ ] Dadas facturas emitidas y recibidas registradas en un ejercicio, cuando el administrador consulta el libro registro de facturas emitidas de ese ejercicio, entonces obtiene el listado detallado de cada factura con fecha, número, NIF del tercero, nombre, base imponible, tipo IVA, cuota IVA, tipo IRPF, cuota IRPF y total.
- [ ] Dado el libro registro de facturas recibidas de un ejercicio, cuando el administrador lo consulta, entonces obtiene el listado detallado de cada factura con fecha, número de factura del proveedor, NIF del proveedor, nombre, base imponible, tipo IVA, cuota IVA, tipo IRPF, cuota IRPF y total.
- [ ] Dado un ejercicio ya consultado, cuando el administrador consulta el mismo libro registro de nuevo, entonces obtiene el mismo resultado sin duplicar.

## Plan
- Leer facturas emitidas de un ejercicio y mapear cada una a una fila del libro registro con sus datos fiscales y del tercero.
- Leer facturas recibidas de un ejercicio y mapear cada una a una fila del libro registro con sus datos fiscales y del tercero.
- Devolver ambos listados (emitidas y recibidas) con el ejercicio consultado y los totales por tipo de documento.
- Asegurar que repetir la consulta del mismo ejercicio devuelve el mismo resultado sin duplicar.

## Fuera de alcance
- Generar el fichero oficial del Modelo 340/347 ante la administración.
- Exportar a PDF/CSV/Excel (historia #13).
- Incluir asientos del libro diario que no sean facturas.

## Sugerencias (opcional)
- Ninguna por ahora.
