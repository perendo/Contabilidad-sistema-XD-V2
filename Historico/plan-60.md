## Story
Como administrador, quiero que el Modelo 347 tenga desglose trimestral y excluya facturas con retención de IRPF para cumplir con la AEAT.

## Acceptance criteria
- [ ] Dado que hay facturas emitidas y recibidas en un ejercicio, algunas con retención de IRPF y otras sin ella, cuando el administrador consulta el Modelo 347, entonces las facturas con retención de IRPF no se incluyen en el importe total anual ni en ningún trimestre del desglose.
- [ ] Dado que hay operaciones repartidas a lo largo del ejercicio, cuando el administrador consulta el Modelo 347, entonces la respuesta incluye el importe desglosado por trimestre (T1, T2, T3, T4) para cada tercero que supere el umbral.
- [ ] Dado un umbral y un ejercicio, cuando el administrador consulta el Modelo 347, entonces solo se incluyen terceros cuyo importe total anual (excluyendo facturas con retención de IRPF) supere el umbral configurado.

## Plan
- Excluir del cálculo las facturas emitidas y recibidas que tengan `irpf_rate` o `irpf_amount` distintos de nulo/cero.
- Calcular el importe por trimestre basándose en el mes de la fecha de cada factura (Q1: ene-mar, Q2: abr-jun, Q3: jul-sep, Q4: oct-dic).
- Añadir el desglose trimestral al esquema de respuesta del Modelo 347 por cada tercero.
- Mantener el cálculo solo con SQL (`SUM`/`GROUP BY`/`UNION ALL`), el umbral, el aislamiento por sociedad activa y el rango del ejercicio.
- Cubrir el nuevo comportamiento con pruebas de integración del endpoint y la exportación CSV.

## Out of scope
- Cambiar el modelo de facturas ni los campos `irpf_rate`/`irpf_amount` existentes.
- Generar el fichero oficial de presentación ante la AEAT ni envío telemático.
- Validación o cotejo con datos de la AEAT.
- Cambios en el frontend ni en la cabecera común (#61).

## Suggestions (your call)
- Reutilizar la consulta SQL existente (UNION ALL entre facturas emitidas y recibidas) añadiendo el filtro IRPF y el desglose por trimestre mediante `CASE WHEN` en SQL, sin cargar filas en memoria.
