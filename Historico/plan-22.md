## Historia
Como administrador, quiero importar facturas recibidas desde documento (PDF/XML) y extraer automáticamente los datos del proveedor para generar el asiento contable, para agilizar el registro de compras/gastos. Requiere: #5, #15, #16

## Criterios de aceptación
- [ ] Dado un fichero XML FacturaE válido, cuando lo importo, entonces se crea la factura recibida (reutilizando el tercero del proveedor si su NIF ya existe, o creándolo automáticamente si no), se genera y acepta su asiento contable y se adjunta el XML al asiento.
- [ ] Dado un XML FacturaE con datos faltantes o inválidos (NIF, número, fecha, base/IVA), cuando lo importo, entonces la petición se rechaza (400) con detalle y no se crea nada.
- [ ] Dado un proveedor cuyo NIF es nuevo, cuando la importación tiene éxito, entonces la respuesta avisa de que se ha creado automáticamente el tercero/proveedor.

## Plan
- Añadir un endpoint que acepta un fichero XML multipart, parsea la estructura FacturaE y valida los campos extraídos.
- Reutilizar la búsqueda de tercero por NIF/CIF; si no existe, crearlo automáticamente (y su subcuenta vinculada), avisando al usuario.
- Reutilizar el flujo de creación de factura recibida (y su asiento aceptado) con los datos extraídos, adjuntando el fichero subido.
- Rechazar con 400 ante cualquier error de parseo/validación, sin crear nada.

## Fuera de alcance
- Extracción de texto de PDF (historia separada).
- Revisión/edición de los datos extraídos antes de confirmar.
- Otros formatos XML (UBL, etc.).
- Importación Norma 43 y perfiles de importación (#24, #25).

## Sugerencias (opcional)
- Dividir la historia original #22 en al menos dos: 22a (esta, XML FacturaE) y 22b (PDF con texto extraíble), reutilizando el flujo de 22a.
- Si la creación automática del tercero requiere una nueva subcuenta de detalle, reutilizar la lógica del seed del PGC o exigir el código de cuenta del proveedor; en caso contrario, fallar con mensaje claro.