## Historia
Como administrador, quiero guardar perfiles de importación por banco, para poder importar extractos con distintas columnas sin cambiar el sistema. Requiere: #18

## Criterios de aceptación
- [ ] Dado un Excel cuyo IBAN ya tiene perfil guardado, cuando se importa, entonces se aplican las columnas del perfil automáticamente y se crean los asientos borrador sin pedir mapeo.
- [ ] Dado un Excel cuyo IBAN no tiene perfil y cuyas cabeceras no coinciden con los alias por defecto, cuando el administrador mapea las columnas de fecha/concepto/importe y confirma, entonces se guarda el perfil y se importan los movimientos.
- [ ] Dado un Excel cuyas cabeceras coinciden con los alias por defecto, cuando se importa, entonces se usa la detección automática (sin perfil) como hasta ahora.

## Plan
- Nueva tabla persistente de perfiles vinculada al IBAN con las columnas mapeadas (fecha, concepto, importe).
- En la importación Excel, intentar primero los alias actuales; si falla, aplicar el perfil guardado para el IBAN; si no hay perfil, devolver un error indicando que se requiere mapeo (con la lista de cabeceras disponibles).
- Endpoint para guardar/actualizar el perfil de un IBAN con el mapeo proporcionado, invocable desde el frontend al confirmar el mapeo.
- En el frontend, cuando la importación falle por falta de mapeo, mostrar los nombres de cabecera detectados y permitir al usuario asignar fecha/concepto/importe, guardando el perfil.
- Reutilizar la vinculación IBAN↔cuenta y la creación de asientos borrador sin cambios.

## Fuera de alcance
- Formatos de fecha y separador decimal personalizados por perfil (solo mapeo de columnas).
- Concatenación de varias columnas en el concepto.
- Norma 43 (usa su propio formato, no perfiles).
- Edición o borrado manual de perfiles desde una pantalla dedicada.

## Sugerencias (opcional)
- Si el mapeo por nombre de cabecera resulta frágil (cabeceras que cambian entre extractos), considerar guardar también el índice de columna como fallback. No implementar ahora; esperar señal real de fallo.