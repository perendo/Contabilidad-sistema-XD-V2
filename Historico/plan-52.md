## Story
Como administrador, quiero que los listados de datos estén paginados para evitar el colapso del servidor y del frontend.

## Acceptance criteria
- [x] Dado un listado con más registros que el tamaño de página, cuando pido una página con `limit` y `offset`, entonces recibo como máximo `limit` registros en orden estable y la página siguiente continúa sin duplicados ni huecos (diario, facturas emitidas, recibidas y pendientes).
- [x] Dado cualquiera de esos listados y el de usuarios, cuando no envío paginación, entonces recibo la primera página con un límite por defecto y un máximo permitido; `limit` o `offset` inválidos devuelven 422.
- [x] Dado el frontend con más registros que una página, cuando uso las tablas de diario, facturas, recibidas, usuarios y cuentas, entonces solo se carga la página visible y puedo avanzar y retroceder.

## Plan
- Aplicar `limit`/`offset` con orden estable, límite por defecto y máximo a diario, facturas emitidas, recibidas, pendientes y usuarios, siguiendo el patrón de cuentas.
- Mantener las respuestas como listas para no romper contratos ni tests existentes.
- Añadir controles anterior/siguiente y tamaño de página fijo en las tablas del frontend.
- Ajustar las cargas de selectores (cuentas y terceros) para pedir el máximo permitido y no quedarse sin opciones.
- Tests de backend para primera página, continuación sin solapes y parámetros inválidos; verificación manual del frontend.

## Out of scope
- Envoltorio de respuesta con `total`, `page` y `pages` (si se quiere, historia aparte).
- Paginación por cursor o scroll infinito.
- Nuevos filtros o búsquedas.
- Informes y listados acotados (libro registro, balances, adjuntos, empresas, terceros).

## Suggestions (your call)
- Reutilizar un helper común de paginación en el backend para no repetir `offset`/`limit` en cada consulta.
- Si más adelante hace falta el total, añadir `X-Total-Count` expuesto por CORS es menos invasivo que cambiar el cuerpo.
