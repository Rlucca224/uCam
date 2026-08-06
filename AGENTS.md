# AGENTS.md

## Reglas permanentes de este proyecto

1. **El modelo no puede VER imágenes.** No soy multimodal: no puedo mirar capturas de pantalla, PNGs, o "ver" resultados visuales. Por lo tanto:
   - **Nunca** intentes capturar screenshots para "verlos tú mismo" (p. ej. con ImageMagick, WidgetPaintable, xwd u otras herramientas de captura).
   - Quando necesites saber cómo se ve algo, usa **medición programática** (coordenadas, tamaños nativos/alloc, propiedades de estilo) o pídele al usuario que mire y describa.
   - Si lees un archivo de imagen con la herramienta Read, NO lo uses para juzgar resultados visuales: no puedo procesar la imagen.

2. **Permiso antes de tocar el sistema o crear archivos.** Antes de ejecutar cualquier comando que modifique algo en el sistema (`sudo`, `apt`, `pip install`, configs, servicios, kill de procesos, etc.) o que cree archivos (fuera de editar los archivos del proyecto que el usuario ya pidió cambiar), **debes pedir permiso al usuario primero**.