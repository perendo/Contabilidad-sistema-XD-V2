## Historia
Como administrador, quiero dar de alta otros usuarios con email y contraseña, para que cada persona acceda con su propia cuenta. Requiere: #1

## Criterios de aceptación
- [ ] Dado un administrador autenticado, cuando crea un nuevo usuario con email y contraseña, entonces el usuario queda registrado y puede iniciar sesión con esas credenciales.
- [ ] Dado un usuario creado, cuando inicia sesión, entonces accede al sistema con su propia sesión independiente del resto.

## Plan
- Añadir un endpoint para crear usuarios con contraseña cifrada, rechazando emails duplicados.
- Exponer el listado de usuarios para que el administrador vea quién tiene acceso.
- Añadir una pantalla mínima para crear y listar usuarios.
- Mantener un único rol: cualquier usuario autenticado puede gestionar usuarios.

## Fuera de alcance
- Identificación del autor en asientos manuales (#35).
- Autoría en asientos generados automáticamente (#36).
- Roles y permisos por usuario.
- Edición, borrado o recuperación de contraseña de usuarios.

## Sugerencias (tu decisión)
- Ninguna.