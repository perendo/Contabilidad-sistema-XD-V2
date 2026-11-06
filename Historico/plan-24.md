## Historia
Como administrador, quiero importar movimientos bancarios desde un fichero Norma 43 CSB asignando al IBAN su cuenta contable del PGC, para revisarlos como asientos en borrador antes de aceptarlos. Requiere: #18

## Criterios de aceptación
- [ ] Dado un fichero Norma 43 CSB válido con IBAN en la cabecera de cuenta y movimientos, cuando el administrador lo sube (con cuenta seleccionada o reutilizando el vínculo guardado del IBAN), entonces el sistema crea un asiento en borrador por cada movimiento, con la cuenta bancaria al debe en los abonos y al haber en los cargos, usando la cuenta 555 como contrapartida, y devuelve el IBAN normalizado y el número de asientos creados.
- [ ] Dado un fichero Norma 43 CSB cuyo IBAN no está vinculado y no se selecciona cuenta, cuando se sube, entonces el sistema rechaza la importación sin crear asientos e indica el IBAN que debe vincularse a una subcuenta de detalle bajo 57.
- [ ] Dado un fichero Norma 43 CSB con alguna fila inválida (fecha de operación o importe mal formado), cuando se sube, entonces el sistema no crea ningún asiento y devuelve las filas con error.

## Plan
- Detectar el formato del fichero subido en el endpoint de importación bancaria (texto Norma 43 frente a Excel) y ramificar el parseo, manteniendo la misma respuesta y validaciones.
- Parsear el fichero Norma 43: extraer el IBAN de la cabecera de cuenta y, por cada movimiento, la fecha de operación, el concepto concatenando los registros complementarios y el importe con su signo (D/H).
- Reutilizar la vinculación IBAN↔cuenta y la creación de asientos borrador con la cuenta 555, validando todas las filas antes de crear nada.
- Validar el IBAN, la cuenta bancaria de detalle y la existencia de la cuenta 555 con los mismos mensajes que en la importación Excel.
- Permitir en la página de importación bancaria subir ficheros de texto (.txt/.csb) además de Excel.

## Fuera de alcance
- Detección de duplicados, vista previa y conversión de divisa (igual que la importación Excel).
- Conversión de CCC a IBAN.
- Adjuntar el fichero CSB al asiento.
- Perfiles de importación por banco (#25).

## Sugerencias (opcional)
- Detectar el formato por contenido (longitud de línea y tipo de registro) en lugar de solo por extensión, para no depender del nombre del fichero.
- Reutilizar un helper común de creación de asientos borrador para que la ruta Norma 43 no duplique la lógica de vinculación y validación.