## Story
Como desarrollador backend, quiero que el código esté organizado en capas separadas (rutas, servicios, repositorios) para facilitar el mantenimiento y la seguridad.

## Acceptance criteria
- [ ] Given el código de un dominio del backend, cuando un desarrollador inspecciona sus archivos, entonces encuentra las definiciones de endpoints HTTP separadas de la lógica de negocio y del acceso a datos.
- [ ] Given una regla de negocio del sistema, cuando un desarrollador busca dónde se aplica, entonces la encuentra definida en un único punto y no repetida en los endpoints.
- [ ] Given el conjunto de tests del backend, cuando se ejecuta la suite, entonces la lógica de negocio y el acceso a datos pueden probarse sin levantar el servidor HTTP.

## Plan
- Inventariar los módulos de dominio actuales del backend y separar rutas HTTP de lógica de negocio y acceso a datos.
- Centralizar el acceso a datos en una capa de repositorio por dominio.
- Agrupar la lógica de negocio en una capa de servicios que use el repositorio.
- Dejar las rutas solo para recibir peticiones, llamar al servicio y devolver respuestas.
- Ejecutar los tests existentes para confirmar que el comportamiento no cambia.

## Out of scope
- Añadir nuevas funcionalidades de negocio ni cambiar el esquema de base de datos.
- Reestructurar el frontend ni modificar los contratos de API externos.
- Escribir tests nuevos más allá de los ya existentes.

## Suggestions (your call)
- Extraer la validación de cuadre de asientos y de cuentas de detalle que ya se repite entre la creación, edición y aceptación de asientos, porque ocurre en varios endpoints.
