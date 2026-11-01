## Historia
Como administrador, quiero iniciar sesión con mi email y contraseña y configurar los datos básicos de mi empresa y el plan de cuentas, para poder empezar a usar el sistema.

## Criterios de aceptación
- [ ] Given un visitante con las credenciales del usuario seed, when introduce email y contraseña válidos, then accede a la aplicación y ve el panel principal.
- [ ] Given un administrador autenticado sin empresa configurada, when introduce los datos básicos de la empresa (nombre fiscal, NIF/CIF, dirección, periodo fiscal), then se guardan y se muestran en la configuración.
- [ ] Given un administrador con empresa configurada, when crea una cuenta del plan de cuentas indicando código, nombre, tipo y cuenta padre opcional, then la cuenta aparece en el listado y puede buscarla por código o nombre.

## Plan
- Autenticación por email+password contra un usuario seed, sin registro público, con sesión para proteger rutas.
- Formulario y persistencia de los datos básicos de la empresa asociados a la cuenta.
- CRUD mínimo de cuentas con código único, nombre, tipo (Activo, Pasivo, Patrimonio Neto, Ingreso, Gasto) y cuenta padre opcional para jerarquía.
- Búsqueda de cuentas por código o nombre.
- Walking skeleton end-to-end: login → configurar empresa → crear cuenta → ver listado.

## Fuera de alcance
- Registro de usuarios, roles y recuperación de contraseña.
- Edición y eliminación de cuentas.
- Importación de un plan de cuentas estándar (PGC).
- Validaciones avanzadas de jerarquía (más de 3 niveles explícitos).
- Multi-empresa.

## Sugerencias
Ninguna por ahora (no hay código previo que indique patrones repetidos).
