## Story
Como administrador, quiero que el extracto de cuenta muestre el saldo inicial correcto para tener una visión real de mis finanzas.

## Acceptance criteria
- [ ] Dado que existen asientos aceptados anteriores a `date_from` en una cuenta, cuando el administrador consulta el extracto de cuenta con ese `date_from`, entonces la respuesta incluye `initial_balance` igual al saldo acumulado de esos asientos previos y el `running_balance` del primer movimiento dentro del rango empieza desde ese saldo inicial.
- [ ] Dado que no se especifica `date_from`, cuando el administrador consulta el extracto de cuenta, entonces `initial_balance` es `0.00` y el `running_balance` empieza desde cero.
- [ ] Dado un extracto de cuenta con `date_from` y `date_to`, cuando se consulta dos veces con los mismos parámetros, entonces `initial_balance` y `final_balance` son idénticos y coherentes con la suma de movimientos del rango.

## Plan
- Calcular el saldo inicial sumando los asientos aceptados de la cuenta anteriores a `date_from`.
- Incluir `initial_balance` en la respuesta del endpoint.
- Iniciar el `running_balance` del primer movimiento del rango desde el saldo inicial.
- Mantener el filtrado por sociedad activa y rango de fechas.
- Cubrir el nuevo comportamiento con pruebas de integración del endpoint.

## Out of scope
- Mostrar saldo inicial en otros informes (balance de sumas y saldos, P&L).
- Edición manual del saldo inicial.

## Suggestions (your call)
- Reutilizar la estructura repositorio → servicio → ruta → esquema que ya se repite en los demás informes.
