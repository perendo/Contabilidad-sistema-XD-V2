## Historia
Como administrador, quiero registrar clientes y proveedores con su NIF/CIF y vincularlos a subcuentas, para generar modelos fiscales (347, IVA, IRPF) con el tercero identificado.

## Criterios de aceptación
- [ ] Given un administrador autenticado, when registra un tercero con nombre o razón social, NIF/CIF, tipo (cliente/proveedor), domicilio fiscal, teléfono, email y subcuenta vinculada, then el sistema lo persiste y lo devuelve con identificador.
- [ ] Given terceros registrados, when se consultan con filtro opcional por tipo o nombre, then se devuelven solo los que coinciden.
- [ ] Given un tercero con subcuenta inexistente o tipo no válido, when se intenta registrar, then el sistema lo rechaza con error.

## Plan
- Modelar terceros en tabla propia, vinculados por account_id a una subcuenta del plan.
- Validar existencia de la subcuenta y tipo permitido antes de persistir.
- Persistir de forma atómica y rechazar envíos inválidos.
- Exponer endpoints autenticados de creación y consulta.
- Soportar filtro opcional por tipo o nombre en la consulta.

## Fuera de alcance
- Edición y eliminación de terceros.
- Vinculación automática en facturas (historias #4 y #5).
- Generación de modelos fiscales (347, IVA, IRPF).
- Adjuntos y otros datos adicionales.

## Sugerencias
- Permitir buscar terceros por NIF/CIF además de nombre, ya que las facturas y modelos fiscales lo necesitarán.
- Restringir account_id como único para que una subcuenta corresponda a un único tercero.