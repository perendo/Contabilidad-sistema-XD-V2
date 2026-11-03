## Historia
Como administrador, quiero identificar terceros que superen el umbral de operaciones, para preparar declaraciones informativas (Modelo 347). Requiere: #4, #5

## Criterios de aceptación
- [ ] Dado un conjunto de facturas emitidas y recibidas con varios terceros en un ejercicio, cuando el administrador consulta el listado de terceros que superan el umbral, entonces obtiene los terceros cuyo total anual de operaciones excede el umbral configurado.
- [ ] Dado un tercero con facturas por debajo y otro por encima del umbral en el mismo ejercicio, cuando se ejecuta la consulta, entonces solo se incluye al tercero que supera el umbral.
- [ ] Dado un ejercicio ya consultado, cuando el administrador consulta el mismo ejercicio y umbral nuevamente, entonces obtiene el mismo resultado sin duplicar.

## Plan
- Leer todas las facturas emitidas y recibidas del ejercicio y agrupar por tercero (NIF/CIF).
- Sumar el importe total de operaciones por tercero en el ejercicio.
- Filtrar los terceros cuyo importe anual supera el umbral configurado.
- Devolver el listado de terceros identificados con su NIF/CIF, nombre y total anual de operaciones.
- Garantizar que repetir la consulta del mismo ejercicio y umbral devuelve el mismo resultado.

## Fuera de alcance
- Generar el fichero del Modelo 347 ante la administración.
- Exportar el listado a PDF/CSV/Excel.
- Configurar un umbral distinto al legal (3.005,06 € anuales).

## Sugerencias (opcional)
- Ninguna por ahora.
