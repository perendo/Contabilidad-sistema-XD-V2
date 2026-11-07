# INFORME DE AUDITORÍA DE SEGURIDAD
## Repositorio: https://github.com/perendo/Contabilidad-sistema-XD-V2

### RESUMEN EJECUTIVO
- Total Vulnerabilidades Críticas: 3
- Total Vulnerabilidades Altas: 4
- Total Vulnerabilidades Medias: 5
- Hallazgos de Escalabilidad: 4
- Cumplimiento Legal PGC / Veri*factu: Brechas detectadas

### DETALLE DE VULNERABILIDADES
#### [SEC-01] Bypass de Aislamiento Multitenant en Lectura/Modificación (IDOR Masivo) (CRITICAL)
- **Archivo:** `backend/app/journal_entries.py` (Líneas 194-196, 240, 266, 295)
- **CWE:** CWE-639 (Insecure Direct Object Reference) / CWE-284
- **Descripción:** En los endpoints de consulta, modificación y anulación de asientos, si 'company_id' es None (por ejemplo, el cliente no envía la cabecera X-Company-Id y no tiene sociedad por defecto asignada), la condición 'if company_id is not None:' se evalúa como False. En consecuencia, el filtro por empresa se omite por completo.
- **Impacto:** Cualquier usuario autenticado puede inspeccionar, modificar, anular o borrar asientos contables y documentos confidenciales de cualquier otra empresa en la base de datos.
- **Remediación:** Sustituir 'active_company_id_dep' (que permite None) por 'require_active_company_id' que rechaza peticiones con 400 Bad Request si no se especifica sociedad, e imponer 'JournalEntry.company_id == company_id' incondicionalmente.

#### [SEC-02] Secuestro de Empresa y Escalada Automática a Administrador (CRITICAL)
- **Archivo:** `backend/app/company.py` (Líneas 70-88)
- **CWE:** CWE-269 (Improper Privilege Management)
- **Descripción:** En el endpoint 'PUT /company', si el usuario no envía la cabecera 'X-Company-Id', el código hace un fallback silencioso obteniendo la primera empresa de la base de datos ('Company.id == 1'). A continuación, si el usuario no es miembro, crea automáticamente un registro CompanyMembership con rol 'admin'.
- **Impacto:** Cualquier usuario recién registrado puede apoderarse de la empresa principal del sistema (ID 1), modificando su NIF, razón social, dirección y configuraciones contables.
- **Remediación:** Eliminar la asignación automática de administradores y el fallback a 'Company.first()'. Exigir ID de empresa explícito en la ruta y validar membresía con rol 'admin'.

#### [SEC-03] Omisión de Tenancy en Liquidación de Facturas (Cobros y Pagos) (CRITICAL)
- **Archivo:** `backend/app/invoices.py & received_invoices.py` (invoices.py:210, received_invoices.py:727)
- **CWE:** CWE-639 (Insecure Direct Object Reference)
- **Descripción:** El endpoint 'POST /invoices/{invoice_id}/pay' busca la factura únicamente por 'Invoice.id == invoice_id' sin contrastar que pertenezca a la sociedad activa del usuario autenticado.
- **Impacto:** Un operador de una empresa puede alterar el estado fiscal y financiero de facturas pertenecientes a otras sociedades y provocar desajustes en sus cuentas contables de tesorería.
- **Remediación:** Vincular incondicionalmente la búsqueda de facturas a 'Invoice.company_id == company_id' y verificar la cuenta de tesorería dentro del mismo contexto societario.

#### [SEC-04] Escalada Vertical: Creación No Restringida de Administradores (HIGH)
- **Archivo:** `backend/app/users.py` (Líneas 35-55)
- **CWE:** CWE-269 (Improper Privilege Management)
- **Descripción:** Cualquier usuario con una sesión válida (sin importar si es un contable raso o un auditor de solo lectura) puede crear usuarios y automáticamente concederles rol de 'admin' en la empresa activa.
- **Impacto:** Un usuario no autorizado puede generar cuentas ficticias con privilegios máximos para perpetuar acceso no supervisado.
- **Remediación:** Implementar un middleware/dependencia 'require_admin' que bloquee el acceso a usuarios sin rol de administración y permitir configurar el rol del nuevo usuario.

#### [SEC-05] Enumeración de Usuarios mediante Ataque de Temporización (Timing Attack) (HIGH)
- **Archivo:** `backend/app/auth.py` (Líneas 28-36)
- **CWE:** CWE-208 (Observable Timing Discrepancy)
- **Descripción:** El método '_authenticate' evalúa 'user is None' antes de 'bcrypt.checkpw'. Si el usuario no existe, retorna en <1ms; si existe pero la contraseña es errónea, tarda ~200ms en procesar el hash bcrypt.
- **Impacto:** Un atacante puede enviar peticiones de login automatizadas y medir el tiempo de respuesta para determinar exactamente qué correos electrónicos están registrados en el sistema.
- **Remediación:** Ejecutar siempre la verificación de hash sobre un hash ficticio precomputado cuando el usuario no existe para mantener el tiempo de cómputo uniforme.

#### [SEC-06] Imposibilidad de Revocar Tokens JWT al Cerrar Sesión (Token Invalidation Gap) (HIGH)
- **Archivo:** `backend/app/auth.py` (Líneas 95-102)
- **CWE:** CWE-613 (Insufficient Session Expiration)
- **Descripción:** El endpoint '/auth/logout' solo elimina las cookies en el cliente mediante cabeceras Set-Cookie con Max-Age=0. El token JWT firmado tiene una validez fija de 1440 minutos (24 horas) y no existe lista negra o tabla de sesiones en base de datos.
- **Impacto:** Cualquier token JWT obtenido por un tercero (por ejemplo, a través de logs, malware o interceptación) continuará siendo plenamente aceptado por el backend durante 24 horas, incluso tras cerrar sesión.
- **Remediación:** Reducir la validez del Access Token a 15-30 minutos, utilizar Refresh Tokens rotatorios y verificar el identificador único del token ('jti') contra una lista de revocación.

#### [SEC-07] Fuga Global de Correos Electrónicos de Usuarios (`GET /users`) (HIGH)
- **Archivo:** `backend/app/users.py` (Líneas 25-30)
- **CWE:** CWE-200 (Exposure of Sensitive Information)
- **Descripción:** El endpoint 'GET /users' devuelve la lista íntegra de usuarios del sistema con sus correos electrónicos sin filtrar por la empresa a la que pertenecen.
- **Impacto:** Un empleado de una sociedad puede descargar el censo completo de emails y usuarios de empresas competidoras alojadas en la plataforma, violando el RGPD.
- **Remediación:** Filtrar el listado de usuarios exclusivamente por las membresías asociadas a la empresa activa.

#### [SEC-08] Procesamiento Inseguro de FacturaE XML (Vulnerabilidad XXE / DoS) (MEDIUM)
- **Archivo:** `backend/app/received_invoices.py` (Líneas 786-860)
- **CWE:** CWE-611 (Improper Restriction of XML External Entity Reference)
- **Descripción:** El parser de FacturaE utiliza 'xml.etree.ElementTree.fromstring()'. Esta implementación nativa no bloquea por defecto la expansión de entidades externas ni ataques cuadráticos de entidades XML (Billion Laughs attack).
- **Impacto:** Un atacante puede subir una factura electrónica manipulada que sature la memoria y CPU del servidor hasta agotarla por completo.
- **Remediación:** Sustituir 'xml.etree.ElementTree' por la biblioteca de parsing blindada 'defusedxml' con 'forbid_dtd=True'.

#### [SEC-09] Falta de Sanitización en Operador LIKE de Terceros (LIKE Injection) (MEDIUM)
- **Archivo:** `backend/app/third_parties.py` (Líneas 95-102)
- **CWE:** CWE-89 (Improper Neutralization of Special Elements)
- **Descripción:** En la búsqueda de terceros, los caracteres '%' y '_' no son escapados antes de construir la cláusula LIKE, a diferencia de 'accounts.py'.
- **Impacto:** Un atacante puede introducir comodines y secuencias de escape que anulen los filtros o fuercen escaneos secuenciales pesados en la base de datos.
- **Remediación:** Implementar escape explícito de comodines SQL en todas las consultas de búsqueda con LIKE/ILIKE.

#### [SEC-10] Almacenamiento Indefinido de Facturas Temporales en Disco (`Data/temp/`) (MEDIUM)
- **Archivo:** `backend/app/received_invoices.py` (Líneas 305-320, 370-385)
- **CWE:** CWE-459 (Incomplete Cleanup)
- **Descripción:** Los archivos temporales y sus ficheros '.meta.json' generados durante la extracción de facturas se escriben en disco pero nunca se borran tras confirmarse la factura.
- **Impacto:** Acumulación masiva de documentación fiscal con datos sensibles en texto plano fuera del esquema de seguridad de base de datos.
- **Remediación:** Eliminar físicamente los archivos temporales inmediatamente tras su procesamiento o mediante un proceso de purga periódica con TTL.

#### [SEC-11] Denegación de Servicio por Bomba de Descompresión en OCR (MEDIUM)
- **Archivo:** `backend/app/received_invoices.py` (Líneas 918-935)
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **Descripción:** Pillow y Pytesseract procesan imágenes sin comprobar previamente las dimensiones totales en píxeles ni manejar la directiva 'MAX_IMAGE_PIXELS'.
- **Impacto:** Un archivo PNG comprimido de 50 KB puede expandirse a cientos de millones de píxeles, provocando un fallo por falta de memoria (OOM crash).
- **Remediación:** Definir un umbral estricto de resolución máxima en píxeles antes de instanciar buffers de imagen en Tesseract.

#### [SEC-12] Cabecera `X-Company-Id` Bloqueada por Política de CORS en FastAPI (MEDIUM)
- **Archivo:** `backend/app/main.py` (Líneas 35-42)
- **CWE:** CWE-942 (Overly Permissive / Mismatched CORS Policy)
- **Descripción:** En 'main.py', la configuración de CORSMiddleware define 'allow_headers=["Authorization", "Content-Type"]', pero omite la cabecera 'X-Company-Id' requerida por la API.
- **Impacto:** Cualquier navegador web que ejecute el frontend en otro puerto u origen verá bloqueadas sus peticiones preflight (OPTIONS) con error de CORS.
- **Remediación:** Añadir 'X-Company-Id' a 'allow_headers' en la configuración de CORSMiddleware.


Generado automáticamente por la Consola de Auditoría.