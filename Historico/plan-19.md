## Historia
Como administrador, quiero aceptar un asiento borrador solo si está cuadrado y revisado, para garantizar la corrección contable. Requiere: #18

## Criterios de aceptación
- [ ] Dado un asiento en borrador cuadrado y marcado como revisado, cuando el administrador lo acepta, entonces su estado pasa a "aceptado".
- [ ] Dado un asiento en borrador que no está cuadrado o no está marcado como revisado, cuando intento aceptarlo, entonces la petición se rechaza (400) y el estado permanece "borrador".
- [ ] Dado un asiento que no está en estado "borrador", cuando intento aceptarlo, entonces la petición se rechaza (400).

## Plan
- Añadir un campo booleano `reviewed` (por defecto falso) al asiento, con su migración.
- Permitir marcar un asiento borrador como revisado (solo borradores).
- Añadir la acción de aceptar que transiciona borrador → aceptado solo si el asiento está cuadrado y revisado, revalidando el cuadre.
- Mantener los asientos aceptados no editables ni anulables (ya garantizado).

## Fuera de alcance
- Apuntes de corrección para asientos aceptados (#20).
- Impedir el borrado de asientos aceptados (#21).
- Importación Norma 43 y perfiles de importación (#24, #25).
- Rediseño del frontend más allá de conectar las acciones de revisar y aceptar.

## Sugerencias (opcional)
- Exponer las acciones de aceptar y revisar con los mismos alias de ruta que el resto (`/journal-entries`, `/entries`, `/asientos`) y verbos en español (`/accept`/`/aceptar`, `/review`/`/revisar`) por consistencia con `/annul`/`/anular`.