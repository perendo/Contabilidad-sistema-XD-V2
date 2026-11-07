## Story
Como administrador, quiero que el sistema valide contraseñas y proteja contra ataques de fuerza bruta y temporización para evitar el acceso no autorizado.

## Acceptance criteria
- [ ] Dada una contraseña de menos de 8 caracteres, cuando se intenta usar, entonces el sistema la rechaza.
- [ ] Dados varios intentos fallidos de inicio de sesión, cuando se supera el límite configurado, entonces el sistema responde `429`.
- [ ] Dado un email que no existe, cuando se intenta iniciar sesión, entonces el sistema tarda un tiempo similar al de un email válido (no revela si existe la cuenta).

## Plan
- Validar la longitud mínima de la contraseña en el alta de usuarios.
- Limitar los intentos fallidos de login y devolver `429` al superar el umbral.
- Ejecutar siempre una comprobación bcrypt (con un hash ficticio cuando el usuario no existe) para evitar ataques de temporización.

## Out of scope
- Bloqueo permanente de cuentas, CAPTCHA y autenticación multifactor.
- Políticas de complejidad de contraseña más allá de la longitud mínima.
