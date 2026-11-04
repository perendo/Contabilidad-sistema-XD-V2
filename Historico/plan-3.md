## Historia
Como administrador, quiero editar o anular asientos en borrador (no aceptados), para corregir errores sin perder trazabilidad.

## Criterios de aceptación
- [ ] Given un asiento en borrador, when el administrador edita fecha, concepto o líneas manteniendo el equilibrio, then el sistema actualiza el asiento y lo devuelve con los nuevos datos.
- [ ] Given un asiento en borrador, when el administrador lo anula, then el asiento permanece en el diario marcado como anulado y no se elimina.
- [ ] Given un asiento aceptado o ya anulado, when se intenta editarlo o anularlo, then el sistema lo rechaza con error.

## Plan
- Añadir estado al asiento (borrador/aceptado/anulado), con aceptado por defecto para los creados en #2.
- Permitir actualización de asientos en borrador revalidando líneas y equilibrio.
- Permitir marcar como anulado un asiento en borrador, sin borrarlo.
- Rechazar modificaciones sobre asientos no borradores.
- Exponer endpoints autenticados de edición y anulación.

## Fuera de alcance
- Edición de asientos aceptados (se corrigen con asiento de corrección, historia #20).
- Bloqueo de borrado físico de aceptados (historia #21).
- Creación de borradores (historia #18) y aceptación (historia #19).
- Adjuntos, tesorería, IVA, IRPF, declaraciones e informes.

## Sugerencias
- Reutilizar la validación de equilibrio y líneas ya existente para la edición, evitando duplicar lógica.