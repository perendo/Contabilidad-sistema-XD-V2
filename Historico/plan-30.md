## Historia
Como administrador, quiero que los datos de cada sociedad (plan de cuentas, asientos, facturas, terceros, IBANs y perfiles) estén completamente aislados, para poder gestionar varias empresas sin mezclar información. Requiere: #1

## Criterios de aceptación
- [ ] Dado dos sociedades con datos distintos, cuando se selecciona la sociedad A, entonces solo se muestran sus asientos, facturas, terceros y plan de cuentas.
- [ ] Dado que se crea una nueva sociedad, entonces sus datos iniciales están vacíos (sin contaminación de otras sociedades).
- [ ] Dado que se cambia la sociedad activa, entonces la configuración de empresa (NIF, nombre) corresponde a la sociedad seleccionada.

## Plan
- Añadir `company_id` (FK a `companies`) a todas las tablas de datos y filtrar todas las consultas por la sociedad activa.
- Introducir el concepto de "sociedad activa" en la sesión (cookie o cabecera), leída en cada petición del backend.
- Garantizar que la creación de cualquier entidad (cuenta, asiento, factura, tercero, IBAN, perfil) asocie automáticamente la sociedad activa.
- Mantener el seed y la configuración de empresa vinculados a la sociedad activa.

## Fuera de alcance
- UI de creación/selección de sociedad (historia 31).
- Migración de datos existentes a una sociedad por defecto (historia 32).
- Aislamiento de documentos adjuntos y perfiles bancarios (historia 33).
- Alta de usuarios y autor del asiento (historia 34).
- Soporte multi-usuario con permisos por sociedad.

## Sugerencias (opcional)
- La sociedad activa puede reutilizar el mismo mecanismo que el ejercicio contable (selector al entrar + cookie), evitando una nueva infraestructura de sesión. Si el selector de ejercicio aún no está implementado en backend, considerar implementar ambos juntos para no duplicar trabajo.
- Si el aislamiento completo en una sola historia resulta demasiado grande, dividir por módulo manteniendo la infraestructura común en la primera.