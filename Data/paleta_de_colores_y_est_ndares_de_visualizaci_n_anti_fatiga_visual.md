# Estándar de Visualización y Paletas Anti-Fatiga Visual (Material 3 Inspired)

Este documento define la guía de colores y estándares de interfaz diseñados para minimizar la fatiga ocular (astenopia) durante jornadas prolongadas de trabajo, manteniendo el cumplimiento de las guías de visualización de **Google Material Design 3** y las normas de accesibilidad **WCAG AA**.

---

## 1. Principios de Ergonomía Visual

1. **Evitar Contraste Absoluto**:
   * **No usar** `#000000` (negro puro) ni `#FFFFFF` (blanco puro) juntos. Provoca el efecto de resplandor o *halation*.
   * Usar tonos marfil/hueso para texto sobre fondos oscuros atenuados.
2. **Saturación Moderada**:
   * Los colores primarios y de acento deben mantenerse desaturados (30% - 50% de saturación) para no forzar la adaptación de la pupila.
3. **Relación de Contraste Óptima**:
   * Mantener la relación de contraste entre **4.5:1** y **7:1** para texto normal (Cumplimiento WCAG AA).

---

## 2. Paletas de Colores Recomendadas

### A. Modo Oscuro Suave (Dark Mode) - *Recomendado para entornos de desarrollo y analítica nocturna*

| Rol de UI | Tono / Nombre | Código HEX | Aplicación / Uso |
| :--- | :--- | :--- | :--- |
| **Fondo Base** | Gris Pizarra Oscuro | `#121212` / `#1E1E2E` | Fondo general de la aplicación. |
| **Superficie / Tarjetas** | Gris Elevado | `#1E1E1E` / `#25263A` | Contenedores, tarjetas, paneles laterales. |
| **Bordes / Separadores** | Gris Neutro Tenue | `#2E2E3E` | Líneas de división y cuadrículas de gráficos. |
| **Texto Principal** | Blanco Hueso / Marfil | `#E1E1E1` | Títulos, cuerpo de texto principal y métricas clave. |
| **Texto Secundario** | Gris Medio | `#A0A0A0` | Etiquetas, leyendas de gráficos y subtítulos. |
| **Acento Primario** | Azul Pastel Desaturado | `#82AFF5` | Botones primarios, serie principal en gráficos. |
| **Éxito / Estado Ok** | Verde Menta Suave | `#7ED9A8` | Indicadores positivos, estados activos. |
| **Alerta / Error** | Rojo Coral Desaturado | `#E57373` | Errores, avisos de alta prioridad. |

---

### B. Modo Claro Cálido (Light Mode) - *Recomendado para uso diurno con iluminación natural*

| Rol de UI | Tono / Nombre | Código HEX | Aplicación / Uso |
| :--- | :--- | :--- | :--- |
| **Fondo Base** | Blanco Crema / Papel | `#F5F5F0` / `#F4F1EA` | Fondo general de la página (elimina el reflejo deslumbrante). |
| **Superficie / Tarjetas** | Blanco Puro | `#FFFFFF` | Tarjetas sobre el fondo crema para dar estructura visual. |
| **Bordes / Separadores** | Gris Claro Cálido | `#E2E8F0` | Líneas suaves de contorno. |
| **Texto Principal** | Azul Noche / Gris Grafito | `#1F2937` / `#2C3E50` | Lectura principal suave pero legible. |
| **Texto Secundario** | Gris Cinc | `#6B7280` | Metadatos y detalles de bajo contraste. |
| **Acento Primario** | Azul Cobalto Suave | `#3B82F6` | Enlaces, elementos interactivos principales. |
| **Éxito / Estado Ok** | Verde Esmeralda Apagado | `#10B981` | Confirmaciones y métricas positivas. |
| **Alerta / Error** | Rojo Terracota | `#EF4444` | Notificaciones de alerta y errores. |

---

## 3. Guía de Aplicación en Gráficos y Data Viz

* **Máximo de colores en un gráfico**: No utilizar más de 5 colores distintos por visualización.
* **Líneas de Guía (Grid Lines)**: Siempre con opacidad reducida (`#2E2E3E` en oscuro, `#E2E8F0` en claro).
* **Barras y Áreas**: Usar opacidades del 70-80% para rellenos, con bordes ligeramente más oscuros o saturados.

---

## 4. Código Listos para Integrar

### Variables CSS (Dark Mode por defecto)

```css
:root {
  /* Dark Mode Ergónico */
  --bg-base: #121212;
  --bg-surface: #1e1e1e;
  --border-color: #2e2e3e;
  --text-primary: #e1e1e1;
  --text-secondary: #a0a0a0;
  
  /* Acentos */
  --accent-primary: #82aff5;
  --status-success: #7ed9a8;
  --status-danger: #e57373;
}

[data-theme="light"] {
  /* Light Mode Cálido */
  --bg-base: #f5f5f0;
  --bg-surface: #ffffff;
  --border-color: #e2e8f0;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  
  /* Acentos */
  --accent-primary: #3b82f6;
  --status-success: #10b981;
  --status-danger: #ef4444;
}
```

### Configuración de Tailwind CSS (`tailwind.config.js`)

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        eyecare: {
          darkBg: '#121212',
          darkSurface: '#1e1e1e',
          lightBg: '#f5f5f0',
          textDark: '#e1e1e1',
          textLight: '#1f2937',
          accentBlue: '#82aff5',
          accentGreen: '#7ed9a8',
          accentRed: '#e57373',
        }
      }
    }
  }
}
```