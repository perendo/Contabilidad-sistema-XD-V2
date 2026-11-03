## Historia
Como administrador, quiero ver el balance de sumas y saldos, para verificar la corrección contable. Requiere: #1, #2

## Criterios de aceptación
- [ ] Dado que existen asientos contables aceptados con apuntes en varias cuentas en un rango de fechas, cuando el administrador consulta el balance de sumas y saldos de ese rango, entonces obtiene para cada cuenta el total del debe, el total del haber y el saldo resultante.
- [ ] Dado que el balance de sumas y saldos se consulta, cuando se calculan los totales globales, entonces la suma de todos los debe es igual a la suma de todos los haber (el asiento cuadrado se verifica).
- [ ] Dado que el balance de sumas y saldos de un rango ya se ha consultado, cuando el administrador lo consulta de nuevo con los mismos parámetros, entonces obtiene el mismo resultado sin duplicar.

## Plan
- Leer los apuntes del libro diario dentro del rango de fechas y agruparlos por cuenta.
- Sumar el debe y el haber de cada cuenta y calcular el saldo (debe menos haber).
- Devolver el listado de cuentas con código, nombre, debe, haber y saldo, junto con los totales globales.
- Verificar que el total de debe es igual al total de haber para confirmar el cuadrado contable.
- Asegurar que repetir la consulta con los mismos parámetros devuelve el mismo resultado.

## Fuera de alcance
- Generar el asiento de cierre o regularización.
- Exportar a PDF/CSV/Excel (historia #13).
- Incluir asientos en borrador o anulados (solo aceptados).

## Sugerencias (opcional)
- Ninguna por ahora.
