# Documentación de la entrega

- `diagrama-componentes.mmd`: fuente Mermaid editable del diagrama.
- `diagrama-componentes.svg`: diagrama vectorial para consultar o exportar.
- `generar_informe.py`: fuente del informe PDF; incluye el diagrama vectorial y el texto.
- `../output/pdf/informe-hito-2.pdf`: informe listo para entregar, enlazado desde el README principal.

## Regenerar el informe

El PDF ya está incluido: no se requieren herramientas adicionales para ejecutar la aplicación. Para editar y regenerar sólo la documentación, usar Python con `reportlab` instalado y ejecutar desde la raíz:

```bash
python docs/generar_informe.py
```

El script produce el PDF y el SVG. Usa DejaVu Sans si está disponible en Windows o Linux y, si no, Helvetica. No accede a la base ni modifica datos de la aplicación. Si cambia la arquitectura, actualizar también la fuente Mermaid y el README principal. Los resultados de verificación escritos en el informe corresponden a la revisión realizada; deben actualizarse al cambiar o volver a probar el sistema.
