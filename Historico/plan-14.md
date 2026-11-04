## Historia
Como administrador, quiero seleccionar el ejercicio contable al entrar al sistema, para poder trabajar con dos ejercicios a la vez durante el cierre de enero. Requiere: #1

## Criterios de aceptación
- [ ] Dado un administrador autenticado con la empresa configurada, cuando entra al sistema, entonces ve en la parte superior un desplegable con el ejercicio activo por defecto (el configurado en la empresa).
- [ ] Dado el desplegable de ejercicio, cuando el administrador lo cambia, entonces el ejercicio activo mostrado en el panel se actualiza y se mantiene durante la sesión.
- [ ] Dado el desplegable, cuando el administrador añade un nuevo ejercicio, entonces queda disponible en la lista y puede seleccionarlo.
- [ ] Dado que cierra sesión, cuando vuelve a iniciar sesión, entonces la selección y la lista de ejercicios añadidos no se recuerdan y se parte del ejercicio configurado en la empresa.

## Plan
- Añadir un desplegable de ejercicio en la barra superior del panel, con el ejercicio configurado por defecto.
- Guardar el ejercicio activo y la lista de ejercicios disponibles en el almacenamiento de sesión del navegador.
- Permitir añadir un nuevo ejercicio desde el propio desplegable.
- Mostrar el ejercicio activo en el panel.
- Limpiar la selección y la lista al cerrar sesión.
- Mantener el backend sin cambios: numeración y filtrado siguen basados en fechas.

## Fuera de alcance
- Cambios en el backend o nuevas APIs para el ejercicio seleccionado.
- Persistir la selección o los ejercicios añadidos en la empresa o en la base de datos.
- Validar que el ejercicio añadido tenga datos contables.
- Usar la selección para filtrar informes o numerar facturas.

## Sugerencias (opcional)
- Usar `sessionStorage` para la selección y la lista, limpiándolos explícitamente en el logout.
