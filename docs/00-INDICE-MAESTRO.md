# HealthTech — Índice Maestro de Documentación

**Proyecto:** Dispensador Inteligente de Medicamentos  
**Versión del índice:** 1.0.0  
**Fecha:** Junio de 2026  
**Autores:** Stefanía García López · Juan Esteban Jiménez Daza  
**Universidad:** Universidad Nacional de Colombia  
**Plataforma:** Raspberry Pi Zero 2W  
**Arquitectura:** Embedded Linux — Monolítica

---

## Estructura General del Proyecto

| #  | Documento                              | Descripción                                                                                                  |
|----|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 00 | `00-INDICE-MAESTRO.md`                 | Mapa general de toda la documentación del proyecto, con descripción y estado de cada entregable.             |
| 01 | `01-DOCUMENTACION-TECNICA-GENERAL.md`  | Visión global, arquitectura del sistema, stack tecnológico, diagramas de componentes y flujo de comunicación. |

---

## Plan de Implementación por Fases

| Fase | Documento                                      | Descripción                                                         | Dependencias     |
|------|------------------------------------------------|---------------------------------------------------------------------|------------------|
| 01   | `fases/fase-01-fundacion.md`                   | Estructura del proyecto, configuración, logging y entorno virtual   | —                |
| 02   | `fases/fase-02-hardware.md`                    | Control GPIO: servo FS90R y sensor de peso HX711                    | Fase 01          |
| 03   | `fases/fase-03-logica-dispensacion.md`         | Scheduler y tolerancia a fallos                                     | Fases 01 y 02    |
| 05   | `fases/fase-05-backend-api.md`                 | API REST FastAPI + WebSocket (endpoints de estado, horarios, logs)  | Fases 01–03      |
| 06   | `fases/fase-06-frontend.md`                    | Dashboard React.js: estado, horarios, historial, dispensación manual | Fase 05         |

---

## Documentación Complementaria Sugerida

Los siguientes documentos no forman parte del alcance actual, pero se recomiendan como extensiones naturales del proyecto a medida que avance la implementación.

| #  | Documento sugerido                     | Descripción                                                                                          | Estado       |
|----|----------------------------------------|------------------------------------------------------------------------------------------------------|--------------|
| 02 | `02-ESPECIFICACION-API.md`             | Contrato detallado de cada endpoint FastAPI: método, ruta, parámetros, respuestas y códigos de error. | Por definir  |
| 03 | `03-MANUAL-HARDWARE.md`               | Guía de ensamblaje físico, esquema de cableado, lista de materiales (BOM) y procedimiento de pruebas. | Por definir  |
| 04 | `04-GUIA-DESPLIEGUE.md`               | Instrucciones paso a paso para instalar y ejecutar el sistema completo en la Raspberry Pi.            | Por definir  |
| 05 | `05-MANUAL-USUARIO.md`                | Guía dirigida al cuidador para configurar horarios, interpretar alertas y usar el dashboard.          | Por definir  |
| 06 | `06-PRUEBAS-VALIDACION.md`            | Plan de pruebas unitarias, de integración y de aceptación con criterios de éxito por requerimiento.   | Por definir  |

---

## Convenciones

- Todos los documentos se redactan en español técnico.
- El formato de entrega es Markdown puro (`.md`).
- Las estructuras de carpetas se representan con árboles ASCII.
- Los bloques de código incluyen identificador de lenguaje (`python`, `bash`, `json`, etc.).
- Los diagramas de arquitectura se representan en texto plano o ASCII art dentro del Markdown.
