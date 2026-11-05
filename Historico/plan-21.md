## Historia
Como administrador, quiero que los asientos aceptados no se puedan borrar, para preservar la trazabilidad. Requiere: #19

## Criterios de aceptación
- [ ] Dado un asiento en borrador, cuando el administrador lo borra, entonces desaparece del libro diario.
- [ ] Dado un asiento aceptado o anulado, cuando intento borrarlo, entonces la petición se rechaza (400) y el asiento permanece.
- [ ] Dado un asiento inexistente, cuando intento borrarlo, entonces la petición se rechaza (404).

## Plan
- Añadir la acción de borrado restringida solo a asientos en borrador (aceptados/anulados se rechazan).
- Eliminar el asiento junto con sus líneas y documentos adjuntos, borrando también los ficheros del disco.
- Exponerla con los alias de ruta habituales y un verbo en español (`/delete`/`/eliminar` o `/borrar`).
- Devolver 204 Sin Contenido en caso de éxito, por consistencia con el borrado de documentos.

## Fuera de alcance
- Borrar asientos aceptados de cualquier forma.
- Borrado en cascada de asientos referenciados (correcciones, facturas).
- Rediseño del frontend más allá de conectar la acción de borrar.

## Sugerencias (opcional)
- Usar `/borrar` como verbo en español por cercanía al dominio ("borradores"), junto a `/delete`/`/eliminar`.
- Limpiar los ficheros de documentos del disco al borrar, replicando `delete_attachment`.