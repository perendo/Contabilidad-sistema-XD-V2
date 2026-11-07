## Story
Como desarrollador backend, quiero que las consultas a la base de datos usen joins eficientes y agregación SQL, para evitar problemas de rendimiento.

## Acceptance criteria
- [x] Dado un periodo con muchas facturas, cuando consulto la liquidación de IVA o el resumen de IRPF (JSON o exportación), entonces obtengo los mismos totales, desglose y contadores que antes y el número de consultas a la base de datos no crece con el número de facturas.
- [x] Dado un ejercicio con muchas facturas de varios terceros, cuando consulto el Modelo 347 con un umbral, entonces aparecen los mismos terceros por encima del umbral con los mismos importes y las consultas no crecen con el número de facturas.
- [x] Dados muchos asientos, líneas y movimientos, cuando consulto el libro registro, el extracto de cuenta o el diario, entonces los datos devueltos son idénticos y el número de consultas no crece con el número de filas.

## Plan
- Unificar el cálculo de IVA, IRPF y 347, hoy duplicado entre los endpoints JSON y las exportaciones.
- Calcular totales, desglose por tipo, contadores y umbral del 347 con `SUM`/`COUNT`, `GROUP BY` y `JOIN` en SQL.
- Cargar tercero y asiento con joins en libro registro y extracto, sin consultas por fila.
- Cargar líneas y autor con eager loading en el listado del diario.
- Añadir tests de equivalencia y de consultas constantes, ejecutar la suite y documentar.

## Out of scope
- Paginación de listados (#52).
- Nuevos índices, caché o migraciones.
- Cambios en el contrato de las respuestas.
- Optimizar rutas de escritura o validaciones.

## Suggestions (your call)
- Helper de test con `before_cursor_execute` para medir consultas, reutilizable en futuras historias de rendimiento.
- Dejar una función de cálculo por informe para que JSON y exportación no vuelvan a divergir.
