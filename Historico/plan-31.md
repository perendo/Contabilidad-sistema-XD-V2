## Historia
Como administrador, quiero crear, editar y seleccionar la sociedad activa al entrar al sistema, para trabajar con una empresa a la vez. Requiere: #1, #30

## Criterios de aceptación
- [ ] Dado un usuario autenticado que entra al sistema, cuando se carga el listado de sociedades, entonces ve todas sus sociedades y puede crear una nueva o seleccionar una para trabajar; si no existe ninguna, se le pide crear una.
- [ ] Dada una o más sociedades, cuando el usuario selecciona una como activa, entonces esa sociedad se usa durante el resto de la sesión y todas las pantallas muestran solo sus datos.
- [ ] Dada una sociedad activa, cuando el usuario edita sus datos básicos (nombre, NIF/CIF, dirección, periodo fiscal), entonces los cambios se guardan y la vista de la sociedad activa los refleja.

## Plan
- Añadir un flujo de entrada/selector que liste las sociedades existentes y permita elegir o crear una antes de llegar al panel.
- Persistir la sociedad seleccionada como activa para las siguientes peticiones API usando el mecanismo existente de cabecera/cookie.
- Reutilizar el formulario de empresa existente para crear y editar, acotado a la sociedad seleccionada.
- Asegurar que cada petición API lleve el identificador de la sociedad activa para que el backend filtre por ella.
- Mantener la selección del ejercicio contable vinculada a la sociedad activa.

## Fuera de alcance
- Aislamiento de datos entre sociedades (ya cubierto por #30).
- Migración de datos existentes a una sociedad por defecto (#32).
- Asociación de documentos y perfiles de importación bancaria a la sociedad activa (#33).
- Alta de usuarios y autoría de asientos (#34).
- Eliminación de sociedades.
- Cambio de sociedad desde dentro de la aplicación (solo se selecciona al entrar).

## Sugerencias (opcional)
- Si más adelante se necesita cambiar de sociedad desde dentro de la aplicación (no solo al entrar), considerar un pequeño selector de sociedad en la barra superior; por ahora, la selección al entrar basta para cumplir los criterios.
- Reutilizar el mismo mecanismo que el ejercicio contable (selector al entrar + cookie), evitando una nueva infraestructura de sesión.