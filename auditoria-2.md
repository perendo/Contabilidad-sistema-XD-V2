📋 Informe de Auditoría Técnica: Contabilidad Sistema XD V2
Repositorio auditado: https://github.com/perendo/Contabilidad-sistema-XD-V2
Stack tecnológico analizado: FastAPI 0.115 + SQLAlchemy 2.0 (PostgreSQL / Alembic) | Next.js 16 + React 19 + Material-UI | Pytesseract / PDFMiner / FPDF2
🎯 Resumen Ejecutivo
El sistema presenta una base funcional interesante para un sistema de contabilidad español (soporte multisociedad, PGC, generación de asientos automáticos a partir de facturas y conciliación bancaria básica). Sin embargo, la auditoría ha revelado vulnerabilidades críticas de seguridad (especialmente en el aislamiento multitenant y control de accesos), cuellos de botella de escalabilidad severos (cómputo de OCR síncrono que bloquea el servidor y consultas masivas sin paginación ni agregación SQL) y deficiencias de diseño arquitectónico y de cumplimiento legal (Ley Antifraude / Veri*factu y PGC).
1. 🛡️ Auditoría de Seguridad
🔴 Crítica: Fuga de Datos y Bypass de Aislamiento Multitenant (IDOR Generalizado)
Bypass mediante company_id is None:
En prácticamente todos los routers de negocio (journal_entries.py, documents.py, extracto_cuenta.py, third_parties.py, invoices.py, received_invoices.py), se encuentra el siguiente patrón:
Python
q = db.query(JournalEntry).filter(JournalEntry.id == entry_id)
if company_id is not None:
  q = q.filter(JournalEntry.company_id == company_id)
entry = q.first()
Code
**Impacto:** Si una petición no incluye la cabecera `X-Company-Id` y el usuario no tiene una sociedad por defecto vinculada, `company_id` se resuelve como `None`. Al ser `None`, **la condición se omite** y la consulta busca directamente por `id` en toda la base de datos sin filtrar por empresa. Cualquier usuario puede visualizar, anular, modificar y descargar documentos de **cualquier empresa del sistema**.
2. **Endpoints sin filtrado de empresa**:
   - En `invoices.py` (Línea 210, `pay_issued_invoice`):
     ```python
     iq = db.query(Invoice).filter(Invoice.id == invoice_id)
     invoice = iq.first()  # ¡Sin verificación de company_id!
Code
Cualquier usuario puede marcar como cobrada una factura emitida de otra empresa ajena.
En received_invoices.py (pay_received_invoice): La misma omisión permite liquidar pagos de facturas recibidas de terceros.
Contaminación cruzada de datos contables:
En invoices.py (create_invoice) y received_invoices.py (_get_or_create_supplier):
third_party = db.query(ThirdParty).filter(ThirdParty.id == body.third_party_id).first()
sales_account = db.query(Account).filter(Account.code == "7000").first()
No se filtra por company_id. Una empresa puede asociar asientos a cuentas contables y terceros pertenecientes a otra sociedad, corrompiendo la contabilidad.
🔴 Crítica: Secuestro de Empresa y Escalada de Privilegios en PUT /company
En company.py (upsert_company):
Python
if company_id is not None:
  company = db.query(Company).filter(Company.id == company_id).first()
else:
  company = db.query(Company).first()
...
if membership is None:
  membership = CompanyMembership(
      user_id=current_user.id, company_id=company.id, role="admin"
  )
  db.add(membership)
Impacto: Cualquier usuario registrado que emita un PUT /company sin la cabecera X-Company-Id obtendrá la primera empresa de la base de datos (Company.id == 1) y el código lo asignará automáticamente como administrador de dicha empresa.
🟠 Alta: Control de Acceso y Gestión de Usuarios Inexistente (RBAC Ausente)
Creación no restringida de administradores: En users.py, cualquier usuario autenticado (incluso un operador básico) puede crear otros usuarios asignándoles rol admin (membership.role = "admin").
Listado global de usuarios: GET /users retorna todos los usuarios de la base de datos sin filtrar por empresa.
Falta de aplicación de roles: Aunque en la tabla company_memberships existe la columna role, no existe ninguna política o dependencia en FastAPI que verifique permisos específicos (p. ej. require_role("admin")).
🟠 Alta: Autenticación, Sesiones y Ataques de Temporización
Ataque de temporización (User Enumeration):
En auth.py:
Python
user = db.query(User).filter(User.email == email).first()
if user is None or not bcrypt.checkpw(
    password.encode(), user.password_hash.encode()
):
  raise HTTPException(401, detail="Credenciales inválidas")
Code
Si el usuario no existe, la respuesta toma < 1 ms. Si existe, la verificación de `bcrypt` toma ~150–250 ms. Esto permite a un atacante listar emails válidos midiendo el tiempo de respuesta.
2. **Tokens JWT sin revocación:**
   El token tiene una validez fija de 24 horas (`1440` minutos). El endpoint `POST /auth/logout` únicamente borra la cookie en el navegador cliente. Si el token fue capturado o almacenado, sigue siendo plenamente utilizable hasta que expire; no hay mecanismo de revocación (*blacklist* o rotación de refresh tokens).
3. **Ausencia de Rate Limiting:**
   No hay limitador de peticiones en `/auth/login` ni `/auth/token`, permitiendo ataques de fuerza bruta continuados contra contraseñas.
4. **Política de contraseñas inexistente:**
   `UserIn` solo valida `password: str`, permitiendo contraseñas de 1 carácter sin comprobación de entropía.

---

### 🟡 Media: Vulnerabilidades en el Procesamiento de Archivos y XML
1. **Riesgo XXE / Billion Laughs en FacturaE**:
   En `received_invoices.py`, se utiliza `xml.etree.ElementTree` nativo (`ET.fromstring(content)`). No mitiga ataques de expansión de entidades XML ni ataques cuadráticos. Debe utilizarse la librería estándar de seguridad `defusedxml`.
2. **Decompression Bomb en OCR**:
   En `_extract_image_text`, se abre la imagen con `PIL.Image.open(BytesIO(content))` sin validar dimensiones máximas (`MAX_IMAGE_PIXELS`), lo que permite que una imagen especialmente manipulada de pocos kilobytes consuma gigabytes de RAM al descomprimirse (Pixel Flood DoS).

---

## 2. ⚡ Escalabilidad y Rendimiento

| Problema | Ubicación | Impacto |
| :--- | :--- | :--- |
| **OCR y Extracción PDF Síncronos** | `received_invoices.py` (`_extract_image_text`, `_extract_pdf_text`) | **Crítico:** Ejecutar Tesseract y PDFMiner en el ciclo de la petición HTTP bloquea los hilos de FastAPI durante 5–25 segundos. Con 3 peticiones simultáneas, el servidor deja de responder. |
| **Cuello de Botella en Numeración de Facturas** | `invoices.py` (`pg_advisory_xact_lock(:year)`) | **Crítico:** El bloqueo es global para todo el año en PostgreSQL; bloquea a **todas las empresas del sistema** simultáneamente al emitir facturas. Además, ¡las empresas comparten la misma secuencia numérica en vez de tener series independientes! |
| **Problema N+1 de Consultas** | `libro_registro.py`, `extracto_cuenta.py`, `journal_entries.py` | **Alto:** Acceder a `inv.third_party` o `line.entry` dentro de bucles sin `joinedload` dispara cientos de consultas SQL independientes. |
| **Agregación en Memoria vs. SQL Engine** | `iva_liquidation.py`, `modelo_347.py` | **Alto:** Descarga todas las facturas del año a objetos Python con `.all()` y las suma con un bucle `sum()`. En lugar de `SELECT SUM(...) GROUP BY`, consume decenas de MB de RAM inútilmente. |
| **Ausencia de Paginación Obligatoria** | `/journal-entries`, `/invoices`, `/third-parties` | **Alto:** Traer 50.000 asientos sin paginar colapsa la memoria del servidor y la interfaz Next.js. |
| **Pool de Conexiones por Defecto** | `database.py` (`create_engine`) | **Medio:** No define `pool_size` ni `max_overflow`. Bajo concurrencia se agota el límite por defecto (5 conexiones) generando errores `QueuePool limit exceeded`. |
| **Descarga de Archivos en Memoria** | `documents.py` (`download_attachment`) | **Medio:** Lee archivos completos de hasta 10 MB a memoria RAM con `read_bytes()`, en lugar de servir en streaming con `FileResponse`. |

---

## 3. 🏗️ Calidad de Arquitectura y Código

### Backend: Controladores Saturados (*Fat Routers*)
- **Falta de arquitectura por capas:** Archivos como `received_invoices.py` superan las 1.000 líneas y mezclan parsing de formatos (FacturaE, PDF, OCR), transacciones de base de datos, validaciones de negocio e I/O de ficheros en las mismas funciones de ruta.
- **Solución:** Reorganizar en:
  - `routers/`: Transporte HTTP, códigos de estado, parámetros FastAPI.
  - `services/`: Lógica de negocio (asientos automáticos, cálculo fiscal, liquidaciones).
  - `repositories/`: Consultas SQLAlchemy y filtros obligatorios por empresa.
  - `tasks/` o *workers*: Procesamiento asíncrono de OCR y FacturaE en segundo plano.

### Antipatrón Financiero: Uso de `float` en Schemas
- Modelos como `BalanceAccountOut`, `InvoiceOut`, `CuentaPerdidasGananciasOut` declaran los importes como `float` en lugar de `Decimal` o cadenas formateadas a 2 decimales.
- El estándar IEEE-754 introduce imprecisiones binarias en operaciones de coma flotante (ej. `0.1 + 0.2 = 0.30000000000000004`), lo cual es inaceptable en contabilidad y auditorías fiscales.

### Frontend (Next.js / React)
- **Código Duplicado en Páginas:** La barra de navegación superior (`AppBar`, selector de empresa, cambio de modo claro/oscuro) está copiada y pegada en casi todas las páginas en lugar de estar centralizada en `layout.tsx` o en un componente `AppShell`.
- **Manejo de Errores Inadecuado:** `api.ts` lanza directamente la cadena de texto devuelta por la API (`throw new Error(text)`), mostrando JSONs serializados de FastAPI en las alertas de la interfaz.
- **Fallo de CORS Preflight con `X-Company-Id`:** El backend define en CORS `allow_headers=["Authorization", "Content-Type"]`. Al no incluir `X-Company-Id`, las llamadas cross-origin desde navegadores fallan en el preflight OPTIONS.

---

## 4. ⚖️ Cumplimiento Legal y Normativo en España

### 1. Ley Antifraude (Ley 11/2021) y Reglamento Veri*factu (RD 1007/2023)
- **Inalterabilidad y Trazabilidad:** La legislación española prohíbe expresamente los sistemas contables o de facturación que permitan modificar o eliminar registros sin dejar una huella inalterable de auditoría.
- **Carencias actuales:**
  - No existe encadenamiento criptográfico (*hash chaining*) entre facturas consecutivas.
  - No hay registro de auditoría (*audit log*) persistente de eventos del sistema.
  - No hay soporte para códigos QR tributarios ni registro de alta y anulación conforme a especificaciones de la AEAT.

### 2. Normativa del Plan General de Contabilidad (PGC)
- **Cuenta de Pérdidas y Ganancias (P&G):** Actualmente solo resta ingresos de gastos. El PGC español exige estructurar el informe distinguiendo obligatoriamente entre **Resultado de Explotación** (cifra de negocios, aprovisionamientos, gastos de personal, amortizaciones) y **Resultado Financiero**.
- **Extracto de Cuenta y Saldo Inicial:** En `extracto_cuenta.py`, si se filtra por una fecha de inicio (`date_from`), el saldo acumulado arranca en 0 sin sumar el saldo de apertura o movimientos anteriores. Esto desvirtúa el saldo contable real.

### 3. Modelo 347 (Operaciones con Terceros)
- **Desglose trimestral:** La AEAT exige declarar el desglose por trimestres (1T, 2T, 3T, 4T) para operaciones superiores a 3.005,06 €. El endpoint actual solo calcula un total anual.
- **Inclusión indebida de facturas con IRPF:** Las facturas de profesionales sujetas a retención ya se declaran en los Modelos 111 y 190, por lo que **deben excluirse del Modelo 347** para no duplicar datos ante la Agencia Tributaria.

---

## 5. 🛠️ Hoja de Ruta de Remediación Recomendada
Prioridad 1 (Urgente - Seguridad & Integridad)
├── 1. Corregir el filtro multi-empresa: forzar 'company_id' obligatorio (error 400/403 si falta).
├── 2. Proteger 'PUT /company' y aislar la creación de usuarios/roles ('require_admin').
├── 3. Habilitar 'X-Company-Id' en 'allow_headers' de CORS en FastAPI.
└── 4. Implementar 'defusedxml' en el parser de FacturaE.
Prioridad 2 (Estabilidad & Rendimiento)
├── 1. Mover la extracción OCR (Tesseract / PDFMiner) a tareas en segundo plano (Celery / BackgroundTasks).
├── 2. Series de facturación aisladas por empresa: '(company_id, year, number)' con bloqueo por empresa.
├── 3. Reemplazar bucles en Python por agregaciones SQL en liquidación de IVA y Modelo 347.
├── 4. Implementar paginación obligatoria y 'joinedload' en asientos y facturas.
Prioridad 3 (Cumplimiento Legal & Arquitectura)
├── 1. Adaptar P&G al esquema oficial del PGC (Resultado de Explotación + Financiero).
├── 2. Corregir el cálculo del saldo anterior en el extracto contable.
├── 3. Añadir desglose trimestral y filtro de exclusión de retenciones en Modelo 347.
└── 4. Refactorizar frontend: Componente 'AppShell' compartido y uso de tipos decimales.
Code