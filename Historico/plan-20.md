## Historia
Como administrador, quiero corregir asientos aceptados mediante un apunte de corrección, para no alterar el histórico. Requiere: #19

## Criterios de aceptación
- [ ] Dado un asiento aceptado, cuando el administrador crea un apunte de corrección que lo referencia con líneas cuadradas, entonces se crea un nuevo asiento aceptado vinculado al original y el original permanece sin cambios y aceptado.
- [ ] Dado un asiento que no está aceptado (borrador o anulado), cuando intento crear un apunte de corrección, entonces la petición se rechaza (400).
- [ ] Dadas líneas descuadradas o cuentas inválidas, cuando intento crear un apunte de corrección, entonces la petición se rechaza (400) y no se crea ningún asiento.

## Plan
- Añadir un campo de vínculo nullable en el asiento hacia el asiento original corregido, con su migración.
- Añadir la acción de corrección que valida que el original esté aceptado y que las líneas sean válidas/cuadradas, y crea un nuevo asiento aceptado vinculado al original.
- Reutilizar la validación existente de líneas y cuentas.
- Dejar el asiento original intocado (sin cambio de estado ni edición).
- Exponer el vínculo en la salida del asiento.

## Fuera de alcance
- Impedir el borrado de asientos aceptados (#21).
- Reversión/reposteo automático del original (solo apunte de ajuste manual).
- Rediseño del frontend más allá de conectar la acción de corregir.

## Sugerencias (opcional)
- Exponer el vínculo bajo varios nombres comunes (`correction_of_entry_id`, `corrects_entry_id`, `original_entry_id`) para facilitar la integración con el frontend y consumidores, ya que el término de dominio es nuevo.
- Ofrecer la acción con los alias de ruta habituales y un verbo en español (`/correct`/`/corregir`), por consistencia con `/accept`/`/aceptar` y `/review`/`/revisar`.