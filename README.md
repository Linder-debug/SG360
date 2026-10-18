# SG360 — Gestión de incidencias de servicios generales

**Autor:** Linder López  
**Proyecto final:** Bootcamp de Azure

## Problema y solución

SG360 centraliza el registro y seguimiento de incidencias de mantenimiento,
limpieza y transporte. Un asistente de IA propone categoría y prioridad,
con una justificación que el usuario revisa antes de registrar el caso.

## Temas del bootcamp aplicados

| Tema | Implementación |
|---|---|
| Almacenamiento en Azure | Azure Table Storage para persistir incidencias. |
| Entra ID y RBAC | Autenticación interactiva y rol Colaborador de datos de la tabla de almacenamiento. |
| Agentes de IA con Foundry | Agente sg360-asistente para sugerir categoría y prioridad con revisión humana. |

## Funcionalidades

- Registrar ubicación, descripción, categoría y prioridad.
- Consultar las incidencias registradas.
- Avanzar estados: Pendiente → En atención → Resuelto.
- Solicitar clasificación asistida por IA.
- Revisar o modificar la propuesta antes de guardar.
- Registrar manualmente cuando la IA no esté disponible.

## Arquitectura

La aplicación Flask se ejecuta en el equipo local y se utiliza desde
el navegador. El backend accede a Azure Table Storage y al agente
de Microsoft Foundry mediante autenticación de Microsoft Entra ID.

La aplicación no requiere incluir claves de almacenamiento en el código.

## Recursos

- Cuenta de almacenamiento: stsg360linder2026.
- Tabla: incidencias.
- Proyecto Foundry: cryptohuerta-7931.
- Agente: sg360-asistente.
- Lenguaje y framework: Python y Flask.

## Ejecución local

Requisitos: Python 3.13 y acceso autorizado a los recursos de Azure
configurados en app.py.

En PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Completar el inicio de sesión cuando se solicite y abrir:
http://127.0.0.1:5000

Para utilizar otra suscripción, adaptar el tenant y los endpoints
en app.py, crear los recursos y asignar los permisos correspondientes.
Clonar el repositorio no concede acceso a los recursos del autor.

## Demostración y evidencias

Las capturas están disponibles en [docs/evidencias](docs/evidencias/).

Se verificó la lectura autorizada de Azure Tables y la respuesta del
agente Foundry desde Python. Para una fuga de agua junto a un tablero
eléctrico, el agente devolvió Mantenimiento, prioridad Alta,
justificación y revisión humana requerida.

Flujo de demostración:

1. Registrar una incidencia desde la aplicación.
2. Comprobar su persistencia en Azure Tables.
3. Avanzar su estado hasta Resuelto.
4. Solicitar una sugerencia de IA para otra incidencia.
5. Revisar categoría y prioridad antes de registrarla.

## Alcance y limitaciones

Prototipo académico con aplicación local y servicios reales de Azure.
El despliegue en App Service quedó bloqueado por cuotas disponibles
de cero en los planes probados; no se presenta como una aplicación
alojada públicamente.

La autenticación interactiva corresponde al desarrollo local.
La clasificación de IA es una recomendación sujeta a revisión humana.

No se incluyen como implementados Bicep, CI/CD ni identidades administradas.
