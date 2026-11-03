## Historia
Como administrador, quiero liquidar el IVA de un periodo (devengado vs. deducible) con saldos a compensar, para cumplir con las obligaciones fiscales. Requiere: #4, #5

## Criterios de aceptación
- [ ] Dadas facturas emitidas y recibidas con IVA registradas en un periodo, cuando el administrador solicita la liquidación de IVA de ese periodo, entonces obtiene el IVA devengado total, el IVA deducible total y el saldo resultante (a ingresar o a compensar).
- [ ] Dada una liquidación de IVA de un periodo, cuando el administrador la consulta, entonces ve el desglose del IVA por tipo impositivo (21 %, 10 %, 4 %, 0 %) de las facturas emitidas y recibidas incluidas.
- [ ] Dada una liquidación de IVA ya generada para un periodo, cuando el administrador solicita la liquidación del mismo periodo de nuevo, entonces obtiene el mismo resultado sin duplicar la liquidación.

## Plan
- Leer las facturas emitidas del periodo y agregar el IVA repercutido (devengado).
- Leer las facturas recibidas del periodo y agregar el IVA soportado (deducible).
- Calcular la diferencia y determinar si el saldo es a ingresar o a compensar.
- Devolver el resumen de liquidación con el desglose por tipo de IVA y el periodo liquidado.
- Asegurar que repetir la liquidación de un periodo ya liquidado devuelve el mismo resultado sin duplicados.

## Fuera de alcance
- Generar el asiento contable de la liquidación en el libro diario.
- Presentar el modelo fiscal ante la administración o exportar la liquidación a PDF/CSV/Excel.
- Gestión de retenciones de IRPF (historia #8).

## Sugerencias (opcional)
- Ninguna por ahora.
