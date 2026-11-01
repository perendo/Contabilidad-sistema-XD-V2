# Especificación de Funcionalidades Básicas para Programa de Contabilidad

Este documento define el alcance mínimo ejecutable (MVP - *Minimum Viable Product*) para la creación de un sistema de gestión contable funcional y estructurado.

## 1. Plan de Cuentas (Libro Mayor)

El núcleo estructural del sistema. Define la jerarquía de cuentas contables para registrar todas las operaciones.

* **Estructura jerárquica:** Creación de cuentas y subcuentas (ej. Nivel 1: Activo, Nivel 2: Clientes, Nivel 3: Cliente X).

* **Atributos de cuenta:**

  * Código único.

  * Nombre o descripción.

  * Tipo (Activo, Pasivo, Patrimonio Neto, Ingreso, Gasto).

* **Búsqueda y filtrado:** Búsqueda rápida por código o nombre de subcuenta.

## 2. Gestión del Libro Diario (Asientos Contables)

Registro cronológico de todas las transacciones económicas de la empresa.

* **Creación de asientos:**

  * Fecha de la operación.

  * Concepto/Descripción general.

  * Múltiples líneas de apunte contable (Subcuenta, Concepto específico, Debe, Haber).

* **Validación de partida doble:** El sistema debe impedir guardar cualquier asiento donde la suma del **Debe** no sea exactamente igual a la suma del **Haber**.

* **Edición y eliminación:** Modificación de asientos no consolidados o anulaciones mediante asiento contable inverso (asiento de rectificación).

## 3. Registro de Facturación (Emitidas y Recibidas)

Gestión simplificada de compras y ventas alineada con el Libro Diario.

* **Facturas Emitidas (Ventas):**

  * Asignación a cliente/subcuenta.

  * Base imponible, tipo de IVA/impuesto aplicado e importe total.

  * Generación automática del asiento contable de venta.

* **Facturas Recibidas (Compras/Gastos):**

  * Asignación a proveedor/subcuenta.

  * Registro de gastos y cuotas soportadas de IVA/impuestos.

  * Generación automática del asiento contable de gasto.

## 4. Gestión de Tesorería Básica (Cobros y Pagos)

Control del estado de las facturas y flujo de caja diario.

* **Control de vencimientos:** Marcado de facturas como *Pendiente*, *Pagada* o *Cobrada*.

* **Asientos de tesorería:** Generación del apunte bancario o de caja al registrar el pago o cobro de una factura.

## 5. Liquidación e Impuestos

Cálculo y gestión automática de las obligaciones fiscales periódicas a partir de las facturas y asientos registrados.

* **Liquidación de IVA (ej. Modelo 303 / 390):**
  * Cálculo del IVA devengado (repercutido) frente al IVA deducible (soportado).
  * Control de saldos a compensar de periodos anteriores.
  * Generación automática del asiento contable de regularización/cierre de IVA del periodo.

* **Gestión de Retenciones e IRPF (ej. Modelos 111, 115):**
  * Desglose de retenciones en facturas de profesionales, alquileres y nóminas.
  * Generación de resúmenes trimestrales y listas para declaraciones informativas anuales.

* **Declaraciones Informativas de Operaciones con Terceros (ej. Modelo 347):**
  * Identificación automática de clientes o proveedores con volumen de operaciones superior al umbral regulatorio (ej. 3.005,06 €).

* **Libros Registro Fiscales:**
  * Generación de los Libros Registro de Facturas Emitidas y Facturas Recibidas conforme a los requerimientos de la administración pública.

## 6. Informes Financieros Esenciales

Reportes clave requeridos para evaluar la situación financiera de la empresa.

* **Balance de Sumas y Saldos (Comprobación):**

  * Muestra todas las cuentas con su saldo inicial, suma del Debe, suma del Haber y saldo final.

* **Pérdidas y Ganancias (P&G):**

  * Cálculo de Ingresos menos Gastos en un rango de fechas para obtener el resultado del ejercicio (beneficio o pérdida).

* **Extracto de Cuenta:**

  * Listado completo de todos los movimientos registrados en una subcuenta específica.

* **Exportación de datos:** Opción para exportar los informes a formatos estándar como PDF o CSV/Excel.

## 7. Configuración General

* **Datos de la empresa:** Nombre fiscal, NIF/CIF, dirección y periodo fiscal.

* **Control de acceso:** Autenticación básica de usuarios (Login/Password) para proteger la información financiera.