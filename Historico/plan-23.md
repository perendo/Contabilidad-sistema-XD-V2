## Historia
Como administrador, quiero exportar la liquidación de IVA de un periodo a PDF, CSV o Excel, para compartir la liquidación externamente. Requiere: #13, #7

## Criterios de aceptación
- [ ] Dado un periodo con facturas emitidas y recibidas, cuando el administrador exporta la liquidación de IVA en CSV, PDF o XLSX, entonces se descarga un fichero cuyo contenido refleja el IVA devengado, el IVA deducible, el saldo, el tipo de saldo y el desglose por tipo de IVA.
- [ ] Dado un periodo sin facturas, cuando el administrador exporta la liquidación de IVA en un formato soportado, entonces se descarga un fichero válido con todos los totales a cero.
- [ ] Dado los mismos parámetros de periodo y formato, cuando el administrador repite la exportación, entonces el fichero descargado es idéntico byte a byte.

## Plan
- Reutilizar el cálculo actual de liquidación de IVA y el patrón de exportación existente para generar CSV, PDF y XLSX descargables.
- Añadir un endpoint de exportación de IVA con los mismos parámetros de periodo y formato que el de balance.
- Asegurar que el fichero incluye los mismos totales y desglose que el informe JSON.
- Mantener la respuesta idempotente y el error para formatos no soportados.
- Registrar la ruta y cubrir con tests análogos a los de exportación de balance.

## Fuera de alcance
- Exportación de IRPF, Modelo 347 y cuenta de pérdidas y ganancias (movidos a #27, #28 y #29).
- Cambios en el cálculo o en los datos de la liquidación de IVA.
- Interfaz de usuario para la descarga (se abordará junto al resto de exportaciones).

## Sugerencias (opcional)
- Cuando se añada el segundo informe, valorar extraer un exportador común para evitar duplicación; por ahora mantener el patrón actual por informe.
- Mantener la convención de nombres y parámetros de `/exportar-balance` para consistencia entre informes.
```<|end|><|start|> assistant to=edit<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="newString">
23. [ ] Como administrador, quiero exportar la liquidación de IVA de un periodo a PDF, CSV o Excel, para compartir la liquidación externamente. Requiere: #13, #7 (IRPF, Modelo 347 y cuenta de pérdidas y ganancias movidos a #27, #28 y #29)
24. [ ] Como administrador, quiero importar movimientos bancarios desde un fichero Norma 43 CSB asignando al IBAN su cuenta contable del PGC, para revisarlos como asientos en borrador antes de aceptarlos. Requiere: #18
25. [ ] Como administrador, quiero guardar perfiles de importación por banco, para poder importar extractos con distintas columnas sin cambiar el sistema. Requiere: #18
26. [x] Como administrador, quiero importar facturas recibidas desde PDF con texto extraíble, extrayendo los datos del proveedor y de la factura para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #22
27. [ ] Como administrador, quiero exportar el resumen trimestral de IRPF a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #8
28. [ ] Como administrador, quiero exportar el Modelo 347 a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #9
29. [ ] Como administrador, quiero exportar la cuenta de pérdidas y ganancias a PDF, CSV o Excel, para compartirla externamente. Requiere: #13, #12