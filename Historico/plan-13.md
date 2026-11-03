## Historia
Como administrador, quiero exportar los informes a PDF, CSV o Excel, para compartirlos externamente. Requiere: #11, #12

## Criterios de aceptación
- [ ] Dado que existe el balance de sumas y saldos de un rango de fechas, cuando el administrador solicita su exportación a CSV, PDF o Excel, entonces recibe un fichero descargable con las columnas de cuenta, debe, haber y saldo, más los totales globales.
- [ ] Dado que el fichero se genera, cuando el administrador lo descarga, entonces su contenido coincide con los datos mostrados en el informe correspondiente.
- [ ] Dado que ya se exportó un informe, cuando se solicita la misma exportación de nuevo, entonces se obtiene el mismo fichero sin duplicar.

## Plan
- Añadir un parámetro de formato a los endpoints de informes existentes para devolver CSV, PDF o Excel.
- Reutilizar la lógica de consulta ya implementada y serializar el resultado al formato solicitado.
- Devolver la respuesta como fichero descargable con el tipo MIME adecuado.
- Garantizar que repetir la exportación devuelve el mismo contenido.

## Fuera de alcance
- Exportar informes distintos al balance de sumas y saldos en esta primera iteración.
- Exportar el libro diario o las facturas (historia #22 cubre importación, no exportación).
- Personalización de plantillas de exportación.

## Sugerencias (opcional)
- Se instalan `fpdf2` (PDF) y `openpyxl` (Excel). CSV usa stdlib (`csv`).
