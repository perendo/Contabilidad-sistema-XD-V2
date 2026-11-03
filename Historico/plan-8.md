## Historia
Como administrador, quiero gestionar retenciones de IRPF en facturas de profesionales, alquileres y nóminas, para preparar resúmenes trimestrales. Requiere: #4, #5

## Criterios de aceptación
- [ ] Dadas facturas emitidas y recibidas con retención de IRPF registradas, cuando el administrador consulta el resumen trimestral, entonces obtiene el total de base sujeta a retención, el tipo de retención aplicado y el importe retenido total por trimestre.
- [ ] Dada una factura emitida o recibida, cuando el administrador registra una retención de IRPF sobre ella, entonces el sistema guarda el porcentaje y el importe retenido asociados a esa factura.
- [ ] Dado un resumen trimestral de retenciones de IRPF, cuando el administrador lo consulta dos veces, entonces obtiene el mismo resultado sin duplicar.

## Plan
- Añadir campo de retención de IRPF (porcentaje e importe) a facturas emitidas y recibidas al crearlas.
- Validar que el tipo de tercero corresponda a profesional, alquiler o nómina cuando se aplica retención.
- Calcular el importe retenido a partir de la base y el porcentaje de retención.
- Exponer un endpoint de consulta que devuelva el resumen de retenciones agrupado por trimestre.
- Garantizar que consultar el mismo trimestre dos veces devuelve el mismo resultado.

## Fuera de alcance
- Generar el modelo 110/115/123 ante la administración.
- Exportar el resumen a PDF/CSV/Excel.
- Asiento contable automático de la retención.

## Sugerencias (opcional)
- Ninguna por ahora.
