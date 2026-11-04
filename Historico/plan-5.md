## Historia
Como administrador, quiero registrar facturas recibidas (compras/gastos) con IVA, para que el sistema genere automáticamente el asiento contable.

## Criterios de aceptación
- [ ] Given un administrador autenticado, un proveedor registrado y cuentas de gasto en el plan, when registra una factura recibida con fecha, proveedor, número de factura del proveedor, concepto, base, tipo de IVA (21/10/4/0) y cuenta de gasto, then la factura se guarda y queda listada mostrando proveedor, número, fecha, base, cuota de IVA y total.
- [ ] Given una factura recibida guardada, when se consulta el libro diario, then aparece un asiento aceptado y cuadrado con la base en el debe de la cuenta de gasto elegida, la cuota en el debe de la cuenta de IVA soportado del tipo aplicado (4720/4721/4722/4723) y el total en el haber de la subcuenta del proveedor.
- [ ] Given un proveedor inexistente o que no es de tipo Proveedor, un número de factura vacío, una base no positiva, un tipo de IVA no permitido o una cuenta que no es de gasto, when se intenta registrar la factura, then el sistema la rechaza con error sin crear factura ni asiento.

## Plan
- Modelar la factura recibida con fecha, proveedor, número del proveedor, concepto, base, tipo y cuota de IVA, total, cuenta de gasto y referencia a su asiento, con restricción única por (proveedor, número de factura).
- Incorporar al plan las subcuentas de IVA soportado 4721 (10 %), 4722 (4 %) y 4723 (0 %) junto a la 4720 existente, y mapear cada tipo de IVA a la suya.
- Validar proveedor existente y de tipo Proveedor, número no vacío y no duplicado para ese proveedor, base positiva, tipo de IVA permitido y cuenta de gasto existente, de tipo Gasto y registrable (subcuenta) antes de persistir.
- Crear en la misma transacción el asiento aceptado —base al debe del gasto, cuota al debe del IVA soportado y total al haber del proveedor— reutilizando la creación de asientos existente y compartiendo con las facturas emitidas la búsqueda de tercero, los tipos de IVA permitidos y el redondeo al céntimo. Con IVA 0 % se registra la línea en 4723 con cuota 0,00, igual que hoy hace la 4770 en las emitidas.
- Exponer alta y listado autenticados y añadir la página de facturas recibidas con formulario (proveedor, número, fecha, concepto, base, IVA y cuenta de gasto) y tabla, enlazada desde el panel.

## Fuera de alcance
- Estado de pago, vencimientos y asientos de tesorería (historia #6).
- Liquidación de IVA (#7), retenciones de IRPF (#8), modelo 347 (#9) y libros registro (#10).
- Importación desde PDF/XML (#22) y documentos adjuntos (#16).
- Edición, anulación o numeración interna propia de facturas recibidas.
- Varias líneas de gasto o varios tipos de IVA en una misma factura, descuentos, recargo de equivalencia, inversión del sujeto pasivo y operaciones intracomunitarias.
- Facturas rectificativas y abonos.

## Sugerencias
- El seed del plan inserta las cuentas que falten en cada guardado de empresa (`backend/app/company.py`) y es idempotente, así que las nuevas 4721/4722/4723 aparecen también en bases ya creadas al volver a guardar los datos de empresa.
