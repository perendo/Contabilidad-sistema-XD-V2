## Story
Como desarrollador frontend, quiero estados reutilizables de carga, vacío y error junto con la paginación, para que los listados se comporten igual en toda la aplicación.

## Acceptance criteria
- [ ] Dado que el usuario abre una página de listado (cuentas, diario, facturas, importación bancaria, informes, modelos fiscales, usuarios), cuando la página carga los datos, entonces ve un estado de carga mientras esperan, un estado vacío si no hay datos, o un estado de error si falla la petición.
- [ ] Dado que una lista de datos tiene más elementos de los que caben en una página, cuando el usuario navega, entonces ve controles de anterior/siguiente con orden estable y sin recargar toda la página.
- [ ] Dado que el usuario navega entre distintas páginas de listado, cuando ocurre un error o la lista está vacía, entonces ve el mismo aviso visual y el mismo comportamiento en todas las páginas.

## Plan
- Identificar los estados de carga, vacío y error que se repiten en las páginas de listado
- Extraer un componente reutilizable que renderice cada estado (carga, vacío, error)
- Extraer o consolidar la paginación con anterior/siguiente y orden estable
- Sustituir los bloques duplicados en las páginas de listado por los componentes reutilizados
- Verificar que carga/vacío/error y paginación se comportan igual en todas las páginas

## Out of scope
- Estados de carga/vacío/error en páginas que no son listados (formularios, informes de vista única)
- Filtros o búsqueda avanzada dentro de los listados
- Paginación con números de página (solo anterior/siguiente)
- Cambios en el backend

## Suggestions (your call)
- Componente único de estados de lista: el mismo bloque de carga/vacío/error se repite en al menos doce páginas
- El componente `PaginationBar` ya existe; consolidar su uso en todos los listados que lo necesiten
