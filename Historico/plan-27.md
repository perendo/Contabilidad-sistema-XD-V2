## Historia
Como administrador, quiero exportar el resumen trimestral de IRPF a PDF, CSV o Excel, para compartirlo externamente. Requiere: #13, #8

## Criterios de aceptación
- [ ] Dado un trimestre con facturas con retención de IRPF, cuando el administrador exporta el resumen IRPF en CSV, PDF o XLSX, entonces se descarga un fichero cuyo contenido refleja las bases e importes de Modelo 111 y Pagos a cuenta 130, junto con los contadores de facturas.
- [ ] Dado los mismos parámetros de año, trimestre y formato, cuando el administrador repite la exportación, entonces el fichero descargado es idéntico byte a byte.

## Plan
- Reutilizar el cálculo actual del resumen IRPF y el patrón de exportación existente para generar CSV, PDF y XLSX descargables.
- Añadir un endpoint de exportación de IRPF con los mismos parámetros (year, quarter) y formato que el informe.
- Mantener la respuesta idempotente y el error para formatos no soportados.
- Registrar la ruta y cubrir con tests análogos a los de exportación de balance.

## Fuera de alcance
- Cambios en el cálculo o en los datos del resumen IRPF.
- Interfaz de usuario para la descarga.

## Sugerencias (opcional)
- Mantener la convención de nombres y parámetros de `/exportar-balance` para consistencia entre informes.
```<|end|><|start|> assistant to=write<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="path">
H:\Contabilidad-sistema-XD-V2\Historico\plan-28.md