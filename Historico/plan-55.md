## Story
Como desarrollador frontend, quiero que los errores de la API se muestren de forma legible y sin cerrar la sesión por error, para que el usuario pueda corregir y reintentar sin perder el trabajo.

## Acceptance criteria
- [ ] Dado que envío un formulario con datos rechazados por el backend, cuando la petición falla, entonces veo el mensaje de error del backend y no el JSON en bruto ni un texto genérico.
- [ ] Dado que una página no puede cargar o guardar datos por un fallo de red o del servidor, cuando se muestra el error, entonces sigo en la misma página con mi sesión activa y puedo reintentar.
- [ ] Dado que mi sesión ha caducado, cuando hago una petición, entonces se me lleva a la pantalla de acceso sin mostrarme un error técnico.

## Plan
- Unificar la lectura de errores de las respuestas del backend para extraer el mensaje legible y distinguir la sesión caducada.
- Extraer un componente reutilizable de aviso de error y sustituir los bloques de alerta repetidos en las páginas.
- Mantener al usuario en la página ante fallos de red o del servidor, y redirigir al acceso solo cuando la sesión haya caducado.
- Corregir los puntos que hoy cierran sesión ante cualquier fallo (por ejemplo, el listado de usuarios).
- Comprobar a mano login, usuarios, facturas y un informe con un error forzado.

## Out of scope
- Cabecera común, tablas, formularios y estados de lista reutilizables (historias derivadas).
- Avisos globales tipo toast, límites de error de React o reintentos automáticos.
- Validación de formularios en cliente y traducción de mensajes del backend.
- Cambios en el backend.

## Suggestions (your call)
- Aplicada: componente único de aviso de error para no repetir el mismo bloque de alerta en todas las páginas.

## Historias derivadas (para el backlog)
- Como desarrollador frontend, quiero que todas las páginas compartan una cabecera reutilizable con título, cambio de tema, enlace al panel y salida, para que la navegación sea coherente y no haya que mantener catorce copias.
- Como desarrollador frontend, quiero estados reutilizables de carga, vacío y error junto con la paginación, para que los listados se comporten igual en toda la aplicación.
