## Historia
Como administrador, quiero que cada asiento manual registre el usuario que lo creó, para identificar su autor.

## Criterios de aceptación
- [ ] Dado un usuario autenticado, cuando crea un asiento manual, entonces el asiento queda registrado con ese usuario como autor.
- [ ] Dado un asiento manual con autor, cuando se consulta el libro diario, entonces se muestra el email del usuario que lo creó.
- [ ] Dado un asiento creado antes de este cambio, cuando se consulta el libro diario, entonces sigue siendo visible y muestra "Sin autor".

## Plan
- Guardar el autor en cada asiento manual en el momento de su creación.
- Exponer el email del autor en los datos del asiento que devuelve la API.
- Añadir la columna "Autor" al listado del libro diario.
- Mantener el campo opcional para que los asientos antiguos sigan funcionando y mostrar "Sin autor".
- Añadir la migración de base de datos para el nuevo campo opcional.

## Fuera de alcance
- Autoría en asientos generados automáticamente: facturas, tesorería, importación bancaria y correcciones (#36).
- Filtrar o buscar asientos por autor.
- Editar el autor de un asiento existente.
- Registrar quién modifica, revisa o anula un asiento.

## Sugerencias (tu decisión)
- Ninguna.
