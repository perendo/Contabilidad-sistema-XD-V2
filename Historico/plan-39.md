## Story
Como administrador, quiero configurar un importe umbral a partir del cual una factura requiere aprobación, para que las operaciones de alto riesgo no se registren sin revisión.

## Acceptance criteria
- [ ] Dado un usuario autenticado, cuando configura un importe umbral para la sociedad activa, entonces el sistema lo guarda y lo devuelve en la respuesta.
- [ ] Dado un importe umbral ya configurado, cuando el usuario consulta la configuración de la sociedad activa, entonces el sistema devuelve el importe umbral configurado.
- [ ] Dado un importe umbral inválido (cero o negativo), cuando el usuario intenta configurarlo, entonces el sistema devuelve un error y no guarda nada.

## Plan
- Exponer un endpoint para configurar el importe umbral de aprobación de la sociedad activa.
- Validar que el importe sea positivo antes de guardarlo.
- Persistir el importe umbral asociado a la sociedad activa.
- Devolver el importe umbral configurado en la respuesta de alta.
- Permitir consultar el importe umbral configurado de la sociedad activa.

## Out of scope
- La lógica de bloqueo o ruta de aprobación de facturas por encima del umbral (historias #40 y #41).
- La bandeja de facturas pendientes de aprobación y su trazabilidad (historia #41).
- Umbrales diferentes por tipo de factura, proveedor o concepto.

## Suggestions (your call)
- Guardar el umbral en el modelo de sociedad existente, ya que la configuración vive a nivel de sociedad activa.
