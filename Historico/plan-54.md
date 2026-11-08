## Story
Como administrador, quiero que los importes contables se manejen con precisión decimal para evitar errores en informes fiscales.

## Acceptance criteria
- [ ] Given un asiento contable con líneas de importe, cuando el administrador consulta el asiento por la API, entonces los campos de débito, crédito y saldo se devuelven siempre con exactamente dos decimales.
- [ ] Given un informe financiero (balance, cuenta de pérdidas y ganancias, IVA), cuando el administrador lo consulta o exporta, entonces los importes totales coinciden exactamente con la suma de las líneas individuales (sin desviaciones por redondeo).
- [ ] Given cualquier importe monetario devuelto por la API, entonces nunca aparece con más de dos decimales ni con artefactos de punto flotante (por ejemplo `0.30000000000000004`).

## Plan
- Identificar todos los esquemas de respuesta y reportes que devuelven importes monetarios como `float`.
- Estandarizar la serialización de importes como cadenas con exactamente dos decimales en las respuestas de la API.
- Asegurar que los cálculos de totales en reportes se hagan sobre `Decimal` y no sobre `float`.
- Ejecutar los tests existentes para confirmar que el comportamiento no cambia.
- No cambiar el tipo de columna en la base de datos (ya es `Numeric`).

## Out of scope
- Cambiar el tipo de columna en la base de datos.
- Soportar más de dos decimales en importes contables.
- Modificar el frontend.

## Suggestions (your call)
- `JournalLineOut` ya serializa `Decimal` como string con 2 decimales; ese mismo patrón podría reutilizarse en los demás esquemas que devuelven importes, ya que la conversión a `float` se repite en varios sitios.
