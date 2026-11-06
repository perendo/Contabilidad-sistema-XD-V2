## Historia
Como administrador, quiero que los documentos adjuntos y los perfiles de importación bancaria se asocien a la sociedad activa, para no mezclar archivos ni perfiles entre empresas. Requiere: #30, #31

## Criterios de aceptación
- [ ] Dadas dos sociedades, cuando se adjunta un documento a un asiento de la sociedad A, entonces el fichero se guarda bajo la carpeta de la sociedad A y solo es accesible cuando esa sociedad está activa.
- [ ] Dada la sociedad activa A, cuando se crean perfiles de importación o vínculos IBAN, entonces quedan asociados a A y no aparecen al cambiar a la sociedad B.
- [ ] Dado un cambio de sociedad activa, entonces los documentos y perfiles listados corresponden únicamente a la nueva sociedad.

## Plan
- Resolver la sociedad del documento a partir del asiento al que pertenece, en lugar de usar la primera sociedad de la base de datos, para la ruta de almacenamiento.
- Mantener el filtrado por sociedad activa en los endpoints de documentos y de importación bancaria.
- Conservar la asociación indirecta de los documentos con la sociedad a través del asiento.

## Fuera de alcance
- Migración de documentos antiguos (ya cubierta por #32, usando la primera sociedad).
- Aislamiento general de datos (ya cubierto por #30).
- Alta de usuarios y autoría de asientos (#34).

## Sugerencias (tu decisión)
- Ninguna.