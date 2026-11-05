## Historia
Como administrador, quiero exportar la cuenta de pérdidas y ganancias a PDF, CSV o Excel, para compartirla externamente. Requiere: #13, #12

## Criterios de aceptación
- [ ] Dado un rango de fechas, cuando el administrador exporta la cuenta de pérdidas y ganancias en CSV, PDF o XLSX, entonces se descarga un fichero cuyo contenido refleja los ingresos, gastos, resultado y tipo de resultado.
- [ ] Dado los mismos parámetros de rango y formato, cuando el administrador repite la exportación, entonces el fichero descargado es idéntico byte a byte.

## Plan
- Reutilizar el cálculo actual de la cuenta de pérdidas y ganancias y el patrón de exportación existente para generar CSV, PDF y XLSX descargables.
- Añadir un endpoint de exportación de la cuenta de pérdidas y ganancias con los mismos parámetros (date_from, date_to) y formato que el informe.
- Mantener la respuesta idempotente y el error para formatos no soportados.
- Registrar la ruta y cubrir con tests análogos a los de exportación de balance.

## Fuera de alcance
- Cambios en el cálculo o en los datos de la cuenta de pérdidas y ganancias.
- Interfaz de usuario para la descarga.

## Sugerencias (opcional)
- Mantener la convención de nombres y parámetros de `/exportar-balance` para consistencia entre informes.
```