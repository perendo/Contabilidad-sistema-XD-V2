## Historia
Como administrador, quiero exportar el Modelo 347 a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #9

## Criterios de aceptación
- [ ] Dado un ejercicio y un umbral, cuando el administrador exporta el Modelo 347 en CSV, PDF o XLSX, entonces se descarga un fichero cuyo contenido refleja los terceros que superan el umbral con su NIF/CIF, nombre y total anual.
- [ ] Dado los mismos parámetros de ejercicio, umbral y formato, cuando el administrador repite la exportación, entonces el fichero descargado es idéntico byte a byte.

## Plan
- Reutilizar el cálculo actual del Modelo 347 y el patrón de exportación existente para generar CSV, PDF y XLSX descargables.
- Añadir un endpoint de exportación del Modelo 347 con los mismos parámetros (year, threshold) y formato que el informe.
- Mantener la respuesta idempotente y el error para formatos no soportados.
- Registrar la ruta y cubrir con tests análogos a los de exportación de balance.

## Fuera de alcance
- Cambios en el cálculo o en los datos del Modelo 347.
- Interfaz de usuario para la descarga.

## Sugerencias (opcional)
- Mantener la convención de nombres y parámetros de `/exportar-balance` para consistencia entre informes.
```