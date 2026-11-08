## Story
Como desarrollador frontend, quiero que CORS permita el encabezado X-Company-Id para evitar errores en llamadas entre dominios.

## Acceptance criteria
- [ ] Dado que el frontend está en un origen distinto al backend, cuando el navegador envía una petición con el encabezado `X-Company-Id`, entonces el backend responde con `Access-Control-Allow-Headers` que incluye `X-Company-Id` y la petición no falla por CORS.
- [ ] Dado que una llamada usa `fetchApi` (importación bancaria o exportación de informes), cuando se ejecuta, entonces se incluye el encabezado `X-Company-Id` con la sociedad activa.
- [ ] Dado que `allow_credentials` es true, cuando se envía `X-Company-Id`, entonces el origen permitido no es `*` y la credencial viaja correctamente.

## Plan
- Verificar que `allow_headers` en CORS del backend incluya `X-Company-Id`.
- Asegurar que `fetchApi` envía `X-Company-Id` (y `Content-Type` cuando corresponda) en todas las llamadas.
- Probar preflight OPTIONS con el encabezado personalizado desde el navegador.
- Cubrir con pruebas que el header se envía y que CORS lo permite.
- Documentar en AGENTS.md que CORS permite `X-Company-Id`.

## Out of scope
- Cambiar `allow_origins` a `*` (incompatible con credenciales).
- Añadir otros encabezados personalizados.
- Cambios de autenticación o sesión.

## Suggestions (your call)
- Extraer una función helper para construir los headers comunes (`Content-Type` + `X-Company-Id`) usada tanto por `api()` como por `fetchApi()`.
- Test de integración que haga una petición real con `X-Company-Id` y verifique el header de respuesta CORS.
