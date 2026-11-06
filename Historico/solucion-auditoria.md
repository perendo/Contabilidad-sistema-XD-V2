# Solución de auditoría: automatización de facturas con agente

## Contexto

Sistema contable single-tenant con varias sociedades, en español y EUR. Se añade un flujo de automatización de facturas recibidas con OCR/LLM y aprobación humana antes de registrar operaciones irreversibles.

## Stack

FastAPI + Next.js + PostgreSQL existentes; se añade LangGraph para el flujo del agente y un servicio OCR/LLM (proveedor a decidir en implementación).

## Decisiones costosas

Single-tenant, rol único (cualquier usuario autenticado puede aprobar), solo online, español, EUR.

## Backlog

Continuación del backlog de `AGENTS.md` (#37–#44).

37. Como administrador, quiero subir una factura recibida escaneada (PDF o imagen) y revisar los datos extraídos en un formulario editable, para registrarla sin teclearla y con el documento original adjunto.
38. Como administrador, quiero que el sistema valide el proveedor, la base, el tipo de IVA, la cuota y el total extraídos y me avise de incoherencias antes de confirmar, para evitar errores fiscales. Requiere: #37
39. Como administrador, quiero configurar un importe umbral a partir del cual una factura requiere aprobación, para que las operaciones de alto riesgo no se registren sin revisión. Requiere: #37
40. Como administrador, quiero que las facturas por debajo del umbral y sin avisos se registren automáticamente, para agilizar las facturas habituales. Requiere: #39
41. Como administrador, quiero una bandeja de facturas pendientes de aprobación donde ver el documento original, los datos extraídos y el motivo de la pausa, para aprobarlas o rechazarlas. Requiere: #39
42. Como administrador, quiero que al aprobar una factura se cree el asiento contable y quede registrado quién y cuándo la aprobó, para mantener la trazabilidad. Requiere: #41
43. Como administrador, quiero que las aprobaciones pendientes se conserven al cerrar sesión o reiniciar el sistema, para no perder trabajo. Requiere: #41
44. Como administrador, quiero poder rechazar una factura propuesta indicando el motivo, para corregirla o descartarla. Requiere: #41

## Fuera de alcance

- Cotejo a 3 vías con órdenes de compra y albaranes.
- Sincronización con ERP externos o e-commerce.
- Ejecución de pagos.
