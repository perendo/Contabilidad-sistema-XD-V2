# Conversación: Conversión a gestoría (multisociedad + multiusuario)

Fecha: 2026-11-06

## Resumen

Se planificó la transformación del sistema contable (MVP single-tenant, un solo usuario) hacia un sistema de gestoría que soporte **multisociedad** (varias empresas con datos aislados) y **multiusuario** (alta de usuarios con identificación del autor del asiento). No se escribió código de implementación en esta conversación; solo se refinaron historias y se actualizó el backlog.

## Decisiones tomadas

### Multisociedad
- **Alcance:** varias sociedades aisladas, una activa a la vez (como el selector de ejercicio contable).
- **Auth:** un solo usuario administrador que puede acceder a todas las sociedades (sin permisos por sociedad).
- **Migración:** los datos existentes se asocian a una sociedad por defecto creada a partir de la configuración actual de empresa.
- **Aislamiento:** completo desde el principio (company_id en todas las tablas de datos, filtrado por sociedad activa).

### Multiusuario
- **Alta de usuarios:** el administrador puede dar de alta otros usuarios con credenciales propias.
- **Autor del asiento:** se registra el usuario que ejecuta la acción como autor de los asientos, incluidos los generados automáticamente (facturas, tesorería, importaciones). Requisito del PGC.
- **Acceso:** todos los usuarios acceden a todas las sociedades.
- **Roles:** todos administradores (sin roles diferenciados).

## Historias añadidas al backlog (AGENTS.md)

- **30.** Como administrador, quiero que los datos de cada sociedad (plan de cuentas, asientos, facturas, terceros, IBANs y perfiles) estén completamente aislados, para poder gestionar varias empresas sin mezclar información. Requiere: #1
- **31.** Como administrador, quiero crear, editar y seleccionar la sociedad activa al entrar al sistema, para trabajar con una empresa a la vez. Requiere: #1, #30
- **32.** Como administrador, quiero migrar la configuración y los datos existentes a una sociedad por defecto, para no perder información al activar multisociedad. Requiere: #30, #31
- **33.** Como administrador, quiero que los documentos adjuntos y los perfiles de importación bancaria se asocien a la sociedad activa. Requiere: #30, #31
- **34.** Como administrador, quiero dar de alta otros usuarios con credenciales propias, para que cada persona acceda con su cuenta y se identifique como autor de los asientos (incluidos los generados automáticamente). Requiere: #1, #30

## Historia 30 aprobada (lista para /pair)

### Criterios de aceptación
- [ ] Given dos sociedades con datos distintos, when se selecciona la sociedad A, then solo se muestran sus asientos, facturas, terceros y plan de cuentas.
- [ ] Given que se crea una nueva sociedad, then sus datos iniciales están vacíos (sin contaminación de otras sociedades).
- [ ] Given que se cambia la sociedad activa, then la configuración de empresa (NIF, nombre) corresponde a la sociedad seleccionada.

### Plan
- Añadir `company_id` (FK a `companies`) a todas las tablas de datos y filtrar todas las consultas por la sociedad activa.
- Introducir el concepto de "sociedad activa" en la sesión (cookie o cabecera), leída en cada petición del backend.
- Garantizar que la creación de cualquier entidad (cuenta, asiento, factura, tercero, IBAN, perfil) asocie automáticamente la sociedad activa.
- Mantener el seed y la configuración de empresa vinculados a la sociedad activa.

### Fuera de alcance
- UI de creación/selección de sociedad (historia 31).
- Migración de datos existentes a una sociedad por defecto (historia 32).
- Aislamiento de documentos adjuntos y perfiles bancarios (historia 33).
- Alta de usuarios y autor del asiento (historia 34).
- Soporte multi-usuario con permisos por sociedad.

### Sugerencias
- La sociedad activa puede reutilizar el mismo mecanismo que el ejercicio contable (selector al entrar + cookie).
- Si el aislamiento completo en una sola historia resulta demasiado grande, dividir por módulo manteniendo la infraestructura común en la primera.

## Notas
- El backlog (AGENTS.md) se actualizó con las historias 30-34, todas marcadas como pendientes `[ ]`.
- La historia 30 está aprobada y lista para implementación con `/pair`.
- No se escribió código en esta conversación.
```