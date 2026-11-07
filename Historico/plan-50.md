## Story
Como administrador, quiero que la numeración de facturas sea correlativa y aislada por empresa para cumplir con la normativa tributaria.

## Acceptance criteria
- [x] Dado una sociedad con facturas emitidas en un mismo ejercicio, cuando registro varias facturas válidas (y algún intento rechazado por validación), entonces cada factura recibe el número siguiente sin saltos (`1, 2, 3…`), el intento rechazado no consume número y la descripción muestra `Factura AAAA/NNNN`.
- [x] Dadas dos sociedades distintas, cuando cada una emite su primera factura del mismo ejercicio, entonces ambas reciben el número 1 y las siguientes continúan su propia serie sin influirse entre sí.
- [x] Dadas dos peticiones simultáneas de factura para la misma sociedad y ejercicio, cuando ambas terminan correctamente, entonces obtienen números distintos y consecutivos, sin errores de unicidad ni correlativos repetidos.

## Plan
- Completar el test de secuencia por ejercicio para cubrir también el formato `AAAA/NNNN` en la descripción y el reinicio al cambiar de año.
- Ampliar el test de rechazo para comprobar varios motivos de validación (cliente no válido, base no positiva, IVA no permitido) sin consumir número.
- Reforzar el test de aislamiento multicompañía con la secuencia completa A → B → A dentro del mismo ejercicio.
- Añadir una prueba de concurrencia real contra PostgreSQL que verifique números únicos y consecutivos; ajustar solo lo imprescindible si aparece un hueco (por ejemplo, `company_id` nulo).
- Ejecutar la suite completa, documentar la decisión en `AGENTS.md` y marcar la historia como `[x]`.

## Out of scope
- Prefijos o series configurables por sociedad.
- Numeración de facturas recibidas (ya usa el número del proveedor).
- Renumeración al anular facturas o integración con Veri*factu.

## Suggestions (your call)
- Si en el futuro se necesita más rendimiento, una tabla de secuencias por `(company_id, year)` evitaría el `max()` en cada alta; hoy no hace falta porque el volumen es bajo y el bloqueo ya garantiza corrección.
