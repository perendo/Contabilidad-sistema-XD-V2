## Story
Como administrador, quiero que el sistema valide contraseñas y proteja contra ataques de fuerza bruta y temporización para evitar el acceso no autorizado.

## Acceptance criteria
- [ ] Dado un usuario autenticado, cuando intenta iniciar sesión con una contraseña débil (menos de 8 caracteres), entonces el sistema rechaza el registro o cambio de contraseña con un error.
- [ ] Dado un usuario que intenta iniciar sesión con contraseña incorrecta varias veces seguidas, entonces el sistema bloquea temporalmente el acceso tras varios intentos fallidos.
- [ ] Dado un usuario que intenta iniciar sesión con un email inexistente, entonces el tiempo de respuesta es indistinguible del caso con email válido (evita enumeración de usuarios).

## Plan
- Agregar validación de fortaleza de contraseña (mínimo 8 caracteres) en el registro y cambio de contraseña.
- Implementar rate limiting en `/auth/login` y `/auth/token` para bloquear tras N intentos fallidos.
- Asegurar que el sistema tarde lo mismo independientemente de si el usuario existe o no (usar bcrypt.checkpw siempre, incluso si el usuario no existe).

## Out of scope
- Bloqueo permanente de cuentas (solo bloqueo temporal por tiempo).
- Autenticación de dos factores (2FA).
- Bloqueo por dirección IP (solo por email/usuario).

## Suggestions (your call)
- Reutilizar la librería `passlib` ya instalada en el proyecto para validar fortaleza de contraseña, ya que ya está disponible como dependencia.
