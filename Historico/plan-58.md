## Story
Como administrador, quiero que el informe de Pérdidas y Ganancias siga la estructura del PGC español para cumplir con la normativa contable.

## Acceptance criteria
- [ ] Dado que hay asientos registrados en cuentas de distintos grupos del PGC (ventas, compras, gastos de explotación, etc.), cuando el administrador consulta el informe de Pérdidas y Ganancias para un rango de fechas, entonces la respuesta presenta las cuentas agrupadas por grupo contable del PGC con el importe de cada grupo, no solo totales globales de ingresos y gastos.
- [ ] Dado un informe de Pérdidas y Ganancias con cuentas de explotación y financieras, cuando se genera el informe, entonces incluye los subtotales del PGC (resultado de explotación, resultado financiero y resultado del ejercicio) calculados a partir de las cuentas de cada grupo.
- [ ] Dada una consulta de Pérdidas y Ganancias con los mismos parámetros, cuando se ejecuta dos veces, entonces se obtiene el mismo resultado y los importes de cada grupo coinciden con la suma de las líneas contables correspondientes.

## Plan
- Definir la agrupación de cuentas por grupo PGC (primer dígito del código de cuenta) y las líneas del informe.
- Calcular el importe de cada línea del PGC a partir de los apuntes del diario aceptados dentro del rango de fechas.
- Exponer el informe con las líneas del PGC, sus subtotales y el resultado del ejercicio en la respuesta del endpoint.
- Mantener el filtrado por sociedad activa y rango de fechas, conservando el aislamiento entre sociedades.
- Cubrir el nuevo comportamiento con pruebas de integración del endpoint.

## Out of scope
- Balance general y otras cuentas del PGC fuera de la cuenta de resultados.
- Exportación del P&L a PDF/CSV/Excel (ya existe por la historia #13).
- Cambios en el plan de cuentas ni creación de cuentas.
- Comparativa con ejercicios anteriores.

## Suggestions (your call)
- Reutilizar la estructura existente (repositorio → servicio → ruta → esquema) que ya se repite en los demás informes, en lugar de crear una capa nueva.
