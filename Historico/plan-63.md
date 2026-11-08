## Story
Como administrador, quiero que al caducar mi sesión se borre también el marcador `auth_session` cuando la aplicación usa un dominio de cookie configurado (`COOKIE_DOMAIN`), para que no quede una sesión fantasma ni rebotes entre la aplicación y el acceso.

## Acceptance criteria
- [ ] Dado que la aplicación está configurada con un `COOKIE_DOMAIN`, cuando el backend caduca la sesión (401), entonces el marcador `auth_session` se borra incluyendo el `Domain` de la cookie, evitando que quede una sesión fantasma.
- [ ] Dado que no hay `COOKIE_DOMAIN` configurado, cuando el backend caduca la sesión (401), entonces el marcador `auth_session` se borra con `path=/` como antes, sin romper el comportamiento actual.
- [ ] Dado que el usuario cierra la sesión manualmente (logout), cuando el backend responde exitosamente, entonces el marcador `auth_session` se borra incluyendo el `Domain` si está configurado.

## Plan
- Leer el valor de `COOKIE_DOMAIN` desde el entorno del frontend para usarlo al borrar el marcador `auth_session`.
- Aplicar el atributo `Domain` al borrar `auth_session` en `clearSession()` y en el lector de errores (`parseApiError`) solo cuando esté configurado.
- Cubrir con pruebas unitarias el borrado del marcador con y sin `COOKIE_DOMAIN`.

## Out of scope
- Cambiar la forma en que el backend fija la cookie de sesión.
- Añadir cifrado o firmado al marcador `auth_session`.
- Cambios en el modelo de usuarios o roles.

## Suggestions (your call)
- Extraer una función helper `clearAuthSessionMarker()` que construya el `document.cookie` con o sin `Domain` según la configuración, y reutilizarla en `clearSession` y `parseApiError`.