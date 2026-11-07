## Story
Como administrador, quiero que el sistema valide mi membresía a una empresa para que no pueda acceder a datos de otras empresas.

## Acceptance criteria
- [ ] Dado un usuario autenticado que es miembro de la empresa A, cuando intenta acceder a un endpoint especificando X-Company-Id de la empresa B (de la que no es miembro), entonces el sistema devuelve 403 Forbidden.
- [ ] Dado un usuario autenticado que es miembro de múltiples empresas, cuando accede sin especificar X-Company-Id, entonces el sistema usa la primera empresa a la que pertenece como sociedad activa.
- [ ] Dado un usuario autenticado sin membresía en ninguna empresa, cuando intenta acceder a cualquier endpoint sin especificar X-Company-Id, entonces el sistema devuelve 404 (no hay empresa activa).

## Plan
- Verificar que todos los endpoints de negocio usan `active_company_id_dep` como dependencia.
- Verificar que todas las consultas de lectura/escritura filtran por `company_id`.
- Probar que un usuario sin membresía no puede acceder a ningún recurso sin especificar empresa.
- Probar que un usuario miembro de empresa A no puede acceder a recursos de la empresa B.

## Out of scope
- Creación de nuevas sociedades o terceros (ya cubierta por otras historias).
- Gestión de roles y permisos granulares dentro de una empresa (queda para historias futuras de RBAC).

## Suggestions (your call)
- Reutilizar el endpoint `POST /company` y `GET /companies` existentes para la gestión de membresías, ya que ya están implementados con validación de `company_id`.