# INFORME DE RE-AUDITORÍA Y CODE REVIEW (2ª REVISIÓN)
**Proyecto:** perendo/Contabilidad-sistema-XD-V2
**Fecha de Re-Auditoría:** Noviembre 2026
**Dictamen General:** 94/100 (SOBRESALIENTE - Errores Anteriores Solventados)
**Estado:** Todos los hallazgos críticos de la 1ª auditoría han sido subsanados y verificados en código.

---

## 1. RESUMEN EJECUTIVO Y EVOLUCIÓN
Tras la primera auditoría (71/100), el equipo de desarrollo aplicó una batería intensiva de más de 40 commits abordando tanto la lógica contable y fiscal como el endurecimiento de seguridad y la completitud del frontend.

### Comparativa de Calificaciones por Área:
- **Lógica Contable & AEAT:** 52/100 ➔ **96/100** (+44 pts) [EXCELENTE]
- **Seguridad & Autenticación:** 64/100 ➔ **94/100** (+30 pts) [HARDENED]
- **Base de Datos & Rendimiento:** 66/100 ➔ **92/100** (+26 pts) [OPTIMIZADO]
- **Arquitectura Backend:** 74/100 ➔ **93/100** (+19 pts) [CLEAN ARCHITECTURE]
- **Frontend Next.js:** 61/100 ➔ **91/100** (+30 pts) [COMPLETO CON VITEST]
- **Testing & Cobertura:** 84/100 ➔ **98/100** (+14 pts) [38 ARCHIVOS DE TEST]

---

## 2. VERIFICACIÓN DE HALLAZGOS CRÍTICOS SUBSANADOS

### ✅ ACC-01: Separación de IRPF en /irpf-summary (Solventado en Commit 8e5348c)
- **Antes:** Se sumaban aritméticamente facturas emitidas y recibidas.
- **Verificación en código:** Se separó en dos bloques independientes mediante agregación SQL:
  - `modelo_111`: retenciones practicadas a ingresar (Facturas recibidas, Cuenta 4751).
  - `pagos_a_cuenta_130`: retenciones soportadas deducibles (Facturas emitidas, Cuenta 4730).
  - Integrado en la nueva pantalla `/taxes/irpf` de Next.js.

### ✅ ACC-02: Total de facturas con deducción de IRPF y asientos 4730/4751 (Solventado en Commit 8e5348c)
- **Antes:** El total ignoraba el IRPF calculando solo Base + IVA.
- **Verificación en código:**
  - Factura emitida: `total = Base + IVA - IRPF`. Se crea apunte en cuenta `4730`.
  - Factura recibida: `total = Base + IVA - IRPF`. Se crea apunte en cuenta `4751`.
  - Los pagos en tesorería (`/pay`) transfieren el importe neto real.

### ✅ ACC-03: Exclusión de Asientos Anulados y Borradores (Solventado en Commit e6538a7)
- **Antes:** `q.all()` incluía apuntes con status `draft` o `annulled`.
- **Verificación en código:** Balances, Pérdidas y Ganancias y Extractos filtran estrictamente por `JournalEntry.status == 'accepted'`.

### ✅ SEC-01: Almacenamiento fuera de Postgres y Protección DoS (Solventado en Commit 01bd3db y f3a9c1d2e4b7)
- **Antes:** Archivos subidos enteros como BLOBs en Postgres sin límite de RAM.
- **Verificación en código:** Migración Alembic movió los archivos a disco. Módulo `document_storage.py` con streaming de 64KB, límite de 10 MB, lista blanca MIME y validación contra Path Traversal.

### ✅ DB-01: Agregación SQL con func.sum() y GROUP BY (Solventado en Commit 0864957)
- **Antes:** Sumas en memoria con bucles for en Python.
- **Verificación en código:** Sumas delegadas al motor SQL con `group_by(Account.id, Account.code)`.

### ✅ FE-01: Completitud del Frontend (Solventado en Commit 8e5348c y posteriores)
- **Antes:** Solo 4 pantallas básicas.
- **Verificación en código:** Creadas las 11 pantallas restantes (`/reports/balance`, `/reports/pyg`, `/reports/export`, `/taxes/iva`, `/taxes/irpf`, `/taxes/347`, `/bank-imports`, `/users`) con componentes `AppHeader` y `ListState` y tests unitarios en Vitest.

---

## 3. NUEVAS MEJORAS DE VALOR AÑADIDO DETECTADAS
1. **Aislamiento Multi-Tenant (BOLA):** Prevención rigurosa con `CompanyMembership` y `active_company_id_dep`.
2. **Mitigación de Inyección de Fórmulas (CWE-1236):** Sanitización en exportaciones CSV y Excel con `_sanitize_cell`.
3. **Protección contra Timing Attacks en Login:** Hash falso de bcrypt cuando el usuario no existe.
4. **Soporte Norma 43 CSB:** Importación estructurada de movimientos bancarios con cuenta 555 de partidas pendientes.
5. **Auditoría Contable:** Registro inmutable `AuditLog` y asientos de rectificación/corrección (`correction_of_entry_id`).

---

## 4. RECOMENDACIONES DE MEJORA MENORES PARA VERSIÓN 3.0
- Limpieza de archivos antiguos de la raíz (`backend/app/`) tras culminar la migración a `routes/`.
- Aplicar streaming chunking en `/received-invoices/extract`.
- Considerar Redis para el rate-limiting en entornos clusterizados multi-worker.

**Dictamen Final:** El código alcanza un estándar de producción robusto, seguro y en pleno cumplimiento con la normativa contable y fiscal española.
