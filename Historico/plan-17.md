## Historia
Como administrador, quiero eliminar documentos adjuntos de un asiento, para corregir errores de carga. Requiere: #16

## Criterios de aceptación
- [ ] Dado un documento adjunto a un asiento, cuando el administrador lo elimina (por ruta asociada al asiento o por id directo), entonces deja de aparecer en el listado y su descarga devuelve 404.
- [ ] Dado un asiento aceptado con un documento adjunto, cuando el administrador elimina el documento, entonces el documento se elimina y el asiento permanece intacto.
- [ ] Dado un identificador de documento inexistente, cuando se solicita su eliminación, entonces se devuelve 404 y no se modifica ningún dato.

## Plan
- Añadir manejadores DELETE siguiendo los mismos alias de rutas que subida, listado y descarga.
- Eliminar el documento por id, validando opcionalmente que pertenezca al asiento indicado.
- Devolver 404 si el documento o el asiento no existen.
- Mantener intacto el asiento y el resto de documentos adjuntos.
- Garantizar que una eliminación repetida no corrompe datos (404 en el segundo intento).

## Fuera de alcance
- Eliminar asientos o sus líneas.
- Eliminación masiva de documentos.
- Borrado lógico o versionado de documentos.
- Interfaz de usuario en el frontend (no existe aún).

## Sugerencias (opcional)
- Reutilizar el patrón de alias ya existente para mantener consistencia con los endpoints de subida/listado/descarga.
