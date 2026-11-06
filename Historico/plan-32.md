## Historia
Como administrador, quiero migrar la configuración y los datos existentes a una sociedad por defecto, para no perder información al activar multisociedad. Requiere: #30, #31

## Criterios de aceptación
- [ ] Dada una instalación con datos creados antes de la multisociedad, cuando se ejecuta la migración, entonces todos los datos existentes (plan de cuentas, asientos, facturas, terceros, IBANs, perfiles y documentos) quedan asociados a una sociedad por defecto y se muestran al seleccionarla.
- [ ] Dada una instalación sin sociedad configurada, cuando se ejecuta la migración, entonces se crea una sociedad por defecto y los datos existentes se asignan a ella, sin pérdida de información.
- [ ] Dada la migración ejecutada, cuando el administrador entra y selecciona la sociedad por defecto, entonces ve la configuración y los datos previos tal como estaban.

## Plan
- Añadir un paso de migración que cree una sociedad por defecto si no existe ninguna.
- Rellenar `company_id` en todas las tablas de datos (cuentas, asientos, terceros, facturas emitidas/recibidas, IBANs, perfiles, documentos) usando la sociedad por defecto, solo donde esté vacío.
- Asegurar que la configuración de empresa existente pase a ser la sociedad por defecto.
- Mantener la migración idempotente para no sobrescribir asignaciones ya realizadas.
- Conservar el aislamiento para las sociedades creadas después de la migración.

## Fuera de alcance
- UI de creación/selección de sociedad (ya cubierto por #31).
- Asociación de documentos y perfiles a la sociedad activa (ya cubierto por #33).
- Alta de usuarios y autoría de asientos (#34).
- Eliminación de sociedades.

## Sugerencias (opcional)
- Implementar el backfill como migración de Alembic mantiene la coherencia con el resto de cambios de esquema y facilita su ejecución en producción. Si se prefiere, también puede exponerse como rutina de arranque, pero la migración es más segura y trazable.