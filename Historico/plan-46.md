## Story
Como administrador, quiero gestionar usuarios y asignar roles y sociedades para controlar quién puede acceder a cada empresa.

## Acceptance criteria
- [ ] Dado un usuario autenticado, cuando da de alta un nuevo usuario, entonces el sistema crea el usuario y lo asocia automáticamente a la sociedad activa del creador con rol "admin".
- [ ] Dado un usuario autenticado que es miembro de una empresa, cuando asigna un rol y una sociedad a otro usuario, entonces el sistema crea o actualiza la membresía de ese usuario para esa sociedad con el rol indicado.
- [ ] Dado un usuario autenticado que es miembro de una empresa, cuando consulta la bandeja de facturas pendientes de aprobación, entonces ve solo las facturas de su empresa.
- [ ] Dado un usuario autenticado que es miembro de una empresa, cuando consulta la lista de empresas, entonces el sistema devuelve solo las sociedades a las que pertenece.

## Plan
- Verificar que POST /users crea el usuario y una membresía en la empresa activa con rol "admin".
- Verificar que GET /companies filtra por company_id del usuario autenticado.
- Verificar que PUT /company crea una membresía para el usuario creador si no existe.
- Agregar endpoint para asignar rol y sociedad a un usuario existente si no existe ya.

## Out of scope
- Gestión de permisos granulares por módulo o funcionalidad (queda para historias futuras de RBAC).
- Cambio de rol de un usuario existente (queda para historia futura).

## Suggestions (your call)
- Reutilizar el modelo CompanyMembership y los endpoints existentes de /users, /companies y /company para evitar duplicación.