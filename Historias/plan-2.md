## Historia
Como administrador, quiero crear asientos contables equilibrados con múltiples líneas, para registrar transacciones económicas siguiendo la partida doble.

## Criterios de aceptación
- [ ] Given un administrador autenticado con plan de cuentas cargado, when crea un asiento con al menos dos líneas, cuentas existentes, importes positivos y debe igual a haber, then el sistema lo persiste y lo devuelve con identificador y sus líneas.
- [ ] Given un asiento cuyo debe no iguala al haber o con líneas inválidas, when se intenta crear, then el sistema lo rechaza con error y no persiste nada.
- [ ] Given asientos existentes, when se consultan con un rango de fechas opcional, then se devuelven solo los asientos dentro del rango.

## Plan
- Modelar asientos con múltiples líneas vinculadas a cuentas.
- Validar equilibrio y validez de líneas antes de persistir, de forma atómica.
- Persistir asientos aceptados (equilibrados) y rechazar los inválidos sin efectos parciales.
- Exponer endpoints autenticados de creación y consulta.
- Soportar filtro opcional por rango de fechas en la consulta.

## Fuera de alcance
- Asientos en borrador pendientes de validación (historia #18).
- Aceptación/revisión de borradores (historia #19).
- Corrección de asientos aceptados mediante apunte de corrección (historia #20).
- Bloqueo de borrado de asientos aceptados (historia #21).
- Edición/anulación de asientos no consolidados (historia #3, a revisar con el nuevo ciclo de vida).
- Adjuntos, tesorería, IVA, IRPF, declaraciones e informes.

## Sugerencias
- Mantener el filtro por fechas en la consulta desde el inicio, para no rehacer el endpoint cuando lleguen los informes (#11, #12).