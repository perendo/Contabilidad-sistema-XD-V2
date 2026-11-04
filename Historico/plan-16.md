# Plan - Historia #16

## Story
Como administrador, quiero adjuntar, listar y descargar documentos en un asiento del libro diario, para respaldar la operación y facilitar auditorías.

## Criterios de aceptación
- [ ] Dado un asiento existente, cuando el administrador adjunta un documento, entonces el documento queda asociado al asiento y disponible para su posterior consulta.
- [ ] Dado un asiento con documentos adjuntos, cuando el administrador solicita el listado, entonces obtiene los documentos del asiento con sus datos identificativos (nombre, tipo y tamaño).
- [ ] Dado un documento adjunto a un asiento, cuando el administrador solicita su descarga, entonces recibe el contenido del fichero con su tipo y nombre original.

## Plan
- Añadir una tabla de documentos vinculada al asiento, guardando nombre, tipo, tamaño y contenido.
- Crear endpoints para adjuntar un documento a un asiento, listar los documentos de un asiento y descargar un documento por su identificador.
- Validar que el asiento existe y que el usuario está autenticado; almacenar el contenido en la base de datos para mantener el aislamiento entre tests.
- Devolver metadatos en el listado y el fichero con su tipo y nombre en la descarga.
- No alterar la lógica de creación, edición o anulación de asientos.

## Fuera de alcance
- Eliminación de documentos adjuntos (historia #17).
- Validaciones de tipo/tamaño de fichero, escaneo antivirus o metadatos editables.
- Interfaz de usuario (frontend).
- Asociación de documentos a facturas u otras entidades.

## Sugerencias (tu decisión)
- Almacenar el contenido en la base de datos (LargeBinary) mantiene la coherencia con el aislamiento por test (`drop_all`/`create_all`); si en el futuro los documentos son grandes, valorar almacenamiento en disco con rutas.
