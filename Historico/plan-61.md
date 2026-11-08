## Story
Como desarrollador frontend, quiero que todas las páginas compartan una cabecera reutilizable con título, cambio de tema, enlace al panel y salida, para que la navegación sea coherente y no haya que mantener catorce copias.

## Acceptance criteria
- [ ] Dado que el usuario está en cualquiera de las páginas de la aplicación (plan de cuentas, libro diario, facturas, importación bancaria, informes, modelos fiscales, usuarios, etc.), cuando carga la página, entonces ve la misma cabecera con el título de la sección, el selector de tema, el enlace al panel y el botón de salida.
- [ ] Dado que el usuario hace clic en el enlace al panel desde cualquier página, entonces es redirigido a la página principal (/).
- [ ] Dado que el usuario hace clic en el botón de salida, entonces se cierra la sesión y se redirige a la pantalla de acceso (/login).

## Plan
- Crear un componente `AppHeader` reutilizable que reciba el título de la sección como prop y contenga el `AppBar` con `Toolbar`, título, selector de tema, enlace al panel y botón de salida.
- Sustituir los bloques `<AppBar>` duplicados de las 14 páginas por el componente `AppHeader`, pasando el título correspondiente.
- Verificar que el cambio de tema y el cierre de sesión sigan funcionando igual que antes en cada página.

## Out of scope
- Cambiar el diseño visual de la cabecera más allá de lo que ya existe.
- Añadir nuevos elementos de navegación (breadcrumb, búsqueda, notificaciones).
- Crear un layout común que envuelva el contenido de las páginas (solo la cabecera).
- Cambios en el backend.

## Suggestions (your call)
- Componente único `AppHeader`: el mismo bloque de `<AppBar>` se repite en catorce páginas (ej. `accounts/page.tsx:125`, `journal/page.tsx`, `invoices/page.tsx`, etc.), lo cual es una señal clara de extracción.
