## Historia
Como administrador, quiero ver la cuenta de pérdidas y ganancias y los extractos de cuenta por rango de fechas, para evaluar el rendimiento financiero. Requiere: #1, #2

## Criterios de aceptación
- [ ] Dado que existen asientos aceptados con cuentas de tipo Ingreso y Gasto en un rango de fechas, cuando el administrador consulta la cuenta de pérdidas y ganancias de ese rango, entonces obtiene el total de ingresos, el total de gastos y el resultado (beneficio o pérdida).
- [ ] Dada una cuenta contable y un rango de fechas, cuando el administrador consulta el extracto de cuenta, entonces obtiene los movimientos (fecha, asiento, debe, haber, saldo acumulado) de esa cuenta en el rango.
- [ ] Dado que ya se consultó la cuenta de pérdidas y ganancias o un extracto de cuenta, cuando se consulta de nuevo con los mismos parámetros, entonces se obtiene el mismo resultado sin duplicar.

## Plan
- Leer los apuntes del libro diario dentro del rango de fechas, solo asientos aceptados.
- Clasificar por tipo de cuenta (Ingreso/Gasto) para la P&L y por cuenta individual para el extracto.
- Calcular total ingresos, total gastos y resultado para la cuenta de pérdidas y ganancias.
- Generar el extracto de cuenta con fecha, descripción, debe, haber y saldo acumulado por cuenta solicitada.
- Garantizar idempotencia: misma consulta devuelve mismo resultado.

## Fuera de alcance
- Exportar a PDF/CSV/Excel (historia #13).
- Comparativa entre ejercicios.
- Asientos de ajuste o cierre.

## Sugerencias (opcional)
- Ninguna por ahora.
