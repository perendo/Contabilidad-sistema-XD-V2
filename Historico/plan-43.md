## Story
Como administrador, quiero que las aprobaciones pendientes se conserven al cerrar sesión o reiniciar el sistema, para no perder trabajo. Requiere: #41

## Acceptance criteria
- [ ] Dado que existen facturas pendientes de aprobación, cuando el usuario cierra sesión y vuelve a iniciar, entonces las facturas pendientes siguen visibles en la bandeja.
- [ ] Dado que existen facturas pendientes de aprobación, cuando el sistema se reinicia, entonces las facturas pendientes siguen accesibles con su documento original.
- [ ] Dado que no hay facturas pendientes, cuando el usuario inicia sesión, entonces la bandeja de aprobación está vacía.

## Plan
- Verificar que las facturas pendientes se almacenan en PostgreSQL (no en sesión/memoria).
- Verificar que los documentos originales de las facturas pendientes se guardan en disco y no se eliminan al cerrar sesión.
- Probar que tras logout/login la bandeja de aprobación muestra las mismas facturas pendientes.
- Probar que tras reinicio del sistema (BD y disco intactos) las facturas pendientes siguen accesibles.

## Out of scope
- Persistencia de aprobaciones ya realizadas (esas ya están en ReceivedInvoice + asiento).
- Sincronización de estado entre sesiones simultáneas.
- Cotejo a tres vías ni otras funcionalidades fuera del epic de facturas.

## Suggestions (your call)
- Reutilizar el endpoint `GET /received-invoices/pending` existente para consultar la bandeja tras login, ya que ya lee de PostgreSQL.
