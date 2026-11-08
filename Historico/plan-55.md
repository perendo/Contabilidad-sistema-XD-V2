## Story
Como desarrollador frontend, quiero que los errores de la API se muestren de forma legible y sin cerrar la sesión por error, para que el usuario pueda corregir y reintentar sin perder el trabajo.

## Acceptance criteria
- [ ] Dado que envío un formulario con datos rechazados por el backend, cuando la petición falla, entonces veo el mensaje del backend en lenguaje legible y no el JSON en bruto ni un texto genérico.
- [ ] Dado que una página no puede cargar o guardar datos por un fallo de red o del servidor, cuando se muestra el error, entonces sigo en la misma página con la sesión activa y puedo reintentar sin perder lo escrito.
- [ ] Dado que mi sesión ha caducado, cuando hago una petición, entonces se me lleva a la pantalla de acceso sin mostrarme un error técnico, mientras que un login con credenciales incorrectas sigue mostrando su mensaje sin recargar la página.

## Plan
- Unificar la lectura de las respuestas de error para extraer un mensaje legible y conservar el detalle estructurado cuando lo haya.
- Distinguir la sesión caducada del resto de fallos: solo un 401 cierra la sesión y redirige al acceso, excluyendo el propio intento de login.
- Extraer un aviso de error reutilizable y sustituir los bloques duplicados de las páginas.
- Revisar cargas y envíos para que ningún fallo genérico cierre la sesión, mostrando el error y permitiendo reintentar sin abandonar la página.
- Cubrir el lector de errores con pruebas unitarias: mensaje del backend, lista de validación, fallo de red, 401 y cabeceras enviadas.

## Out of scope
- Cabecera común y estados reutilizables de carga/vacío/error (ya derivados a #61 y #62).
- Avisos globales tipo toast, límites de error de React y reintentos automáticos.
- Validación de formularios en cliente y traducción de mensajes del backend.
- Cierre completo de sesión con dominio de cookie configurado (`COOKIE_DOMAIN`), recogido en #63.
- Cambios en el backend.

## Suggestions (your call)
- Componente único de aviso de error: el mismo bloque de alerta se repite en catorce páginas.
- Botón de reintento en el panel: si falla la carga inicial, hoy no hay forma de reintentar sin recargar el navegador.
- Vitest: no hay runner de tests unitarios en el frontend y el lector de errores es lógica pura fácil de cubrir.
