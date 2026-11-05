## Historia
Como administrador, quiero importar un Excel de movimientos bancarios y vincular su IBAN a una subcuenta del PGC, para que cada movimiento quede como asiento en borrador listo para revisar. Requiere: #2

## Criterios de aceptación
- [ ] Dado un Excel del formato soportado, cuando confirmo la subcuenta del IBAN detectado y la importación, entonces se crea un asiento en borrador por cada movimiento, fechado con la fecha de operación, con el banco al debe en los abonos y al haber en los cargos, y la cuenta 555 como contrapartida.
- [ ] Dado un IBAN ya vinculado a una subcuenta, cuando importo otro Excel del mismo IBAN, entonces se usa esa subcuenta sin volver a pedirla.
- [ ] Dado un Excel con alguna fila con fecha o importe inválido, cuando intento importarlo, entonces no se crea ningún asiento y veo qué filas fallan.

## Plan
- Nueva pantalla de importación bancaria accesible desde el panel.
- Lectura del Excel: localizar la fila de cabecera, extraer fecha de operación, concepto e importe, y detectar el IBAN de la cabecera.
- Registro persistente de la relación IBAN → subcuenta de detalle del PGC, asignable durante la importación.
- Creación transaccional de un asiento borrador por movimiento, con el banco y la 555 como contrapartida.
- Validación completa antes de crear nada, con el detalle de las filas que fallan.

## Fuera de alcance
- Aceptar o editar los borradores (#19).
- Perfiles de importación para otros formatos bancarios (historia #25).
- Conciliación, detección de duplicados y adjuntar el Excel a los asientos.
- Una pantalla independiente para gestionar el mapeo IBAN; se reasigna al importar.

## Sugerencias (opcional)
- La cabecera de página y la comprobación de sesión ya se repiten en todas las pantallas; al añadir otra, podría valorarse extraer un layout común.
