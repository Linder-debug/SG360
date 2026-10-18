import json
from flask import jsonify
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import AzureError
from openai import APIError

from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, redirect, render_template_string, request, url_for
from azure.identity import InteractiveBrowserCredential
from azure.data.tables import TableClient, UpdateMode
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

credencial = InteractiveBrowserCredential(
    tenant_id="cryptohuertaoutlook.onmicrosoft.com"
)
tabla = TableClient(
    endpoint="https://stsg360linder2026.table.core.windows.net",
    table_name="incidencias",
    credential=credencial
)

CATEGORIAS = ("Mantenimiento", "Limpieza", "Transporte", "Otros")
PRIORIDADES = ("Baja", "Media", "Alta")
PARTICION = "SG360"

PAGINA = '\n<!doctype html>\n<html lang="es">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>SG360 · Incidencias</title>\n    <style>\n        body {font-family: Arial; background: #f3f6fa; color: #183047;\n              max-width: 1100px; margin: 40px auto; padding: 0 20px}\n        .panel {background: white; padding: 24px; border-radius: 12px;\n                margin-bottom: 24px}\n        label {display: block; margin-top: 14px}\n        input, select, textarea {box-sizing: border-box; width: 100%;\n               padding: 10px; margin-top: 6px; border: 1px solid #bbc7d4;\n               border-radius: 6px}\n        button {background: #0067b8; color: white; border: 0;\n                padding: 12px 20px; border-radius: 6px; margin-top: 18px;\n                cursor: pointer}\n        table {width: 100%; border-collapse: collapse}\n        th, td {text-align: left; padding: 12px; border-bottom: 1px solid #ddd}\n        td {overflow-wrap: anywhere}\n        .tabla {overflow-x: auto}\n    </style>\n</head>\n<body>\n    <h1>SG360</h1>\n    <p>Gestión de incidencias de servicios generales · Prototipo académico</p>\n    <section class="panel">\n        <h2>Registrar incidencia</h2>\n        <form method="post" action="{{ url_for(\'registrar\') }}">\n            <label>Ubicación\n                <input name="ubicacion" maxlength="120" required\n                       placeholder="Ejemplo: Comedor principal">\n            </label>\n            <label>Categoría\n                <select name="categoria">\n                    {% for categoria in categorias %}\n                    <option>{{ categoria }}</option>\n                    {% endfor %}\n                </select>\n            </label>\n            <label>Descripción\n                <textarea name="descripcion" maxlength="2000"\n                          rows="3" required></textarea>\n            </label>\n            <label>Prioridad\n                <select name="prioridad">\n                    <option>Baja</option>\n                    <option selected>Media</option>\n                    <option>Alta</option>\n                </select>\n            </label>\n            \n<button type="button" id="sugerir-ia">Sugerir con IA</button>\n<p id="resultado-ia" role="status" style="white-space: pre-wrap"></p>\n<p>Revisa la sugerencia y ajusta los campos antes de registrar.</p>\n<button type="submit">Registrar incidencia</button>\n\n        </form>\n    </section>\n    <section class="panel">\n        <h2>Incidencias registradas: {{ incidencias | length }}</h2>\n        <div class="tabla">\n        <table>\n            <thead>\n                <tr>\n                    <th>Código</th><th>Ubicación</th><th>Categoría</th>\n                    <th>Descripción</th><th>Prioridad</th><th>Estado</th><th>Acción</th>\n                </tr>\n            </thead>\n            <tbody>\n                {% for caso in incidencias %}\n                <tr>\n                    <td>SG-{{ caso.id[:12] | upper }}</td>\n                    <td>{{ caso.ubicacion }}</td>\n                    <td>{{ caso.categoria }}</td>\n                    <td>{{ caso.descripcion }}</td>\n                    <td>{{ caso.prioridad }}</td>\n                    <td>{{ caso.estado }}</td>\n                    <td>\n                        {% if caso.estado != \'Resuelto\' %}\n                         <form method="post"\n                        action="{{ url_for(\'avanzar_estado\', incidencia_id=caso.id) }}">\n                        <input type="hidden" name="estado_actual" value="{{ caso.estado }}"><button type="submit">\n                        {% if caso.estado == \'Pendiente\' %}\n                             Iniciar atención\n                         {% else %}\n                            Marcar resuelto\n                        {% endif %}\n                        </button>\n                        </form>\n                        {% else %}\n                            Atención finalizada\n                            {% endif %}\n                    </td>\n                </tr>\n                {% else %}\n                <tr><td colspan="7">Todavía no hay incidencias.</td></tr>\n                {% endfor %}\n            </tbody>\n        </table>\n        </div>\n    </section>\n\n<script>\nconst botonIA = document.getElementById("sugerir-ia");\nconst resultadoIA = document.getElementById("resultado-ia");\nconst formulario = botonIA.closest("form");\n\nbotonIA.addEventListener("click", async () => {\n    const ubicacion = formulario.elements.ubicacion.value.trim();\n    const descripcion = formulario.elements.descripcion.value.trim();\n\n    if (!ubicacion || !descripcion) {\n        resultadoIA.textContent = "Completa ubicacion y descripcion.";\n        return;\n    }\n\n    botonIA.disabled = true;\n    resultadoIA.textContent = "Consultando al asistente...";\n    try {\n        const respuesta = await fetch("/sugerir-ia", {\n            method: "POST",\n            headers: {"Content-Type": "application/json"},\n            body: JSON.stringify({ubicacion, descripcion})\n        });\n        const datos = await respuesta.json();\n\n        if (!respuesta.ok) {\n            throw new Error(datos.error || "No se pudo obtener la sugerencia.");\n        }\n\n        if (formulario.elements.ubicacion.value.trim() !== ubicacion ||\n            formulario.elements.descripcion.value.trim() !== descripcion) {\n            resultadoIA.textContent =\n                "El texto cambio durante la consulta. Solicita otra sugerencia.";\n            return;\n        }\n\n        if (datos.categoria === null || datos.prioridad === null) {\n            resultadoIA.textContent =\n                "Falta informacion: " + datos.pregunta_aclaratoria;\n            return;\n        }\n\n        formulario.elements.categoria.value = datos.categoria;\n        formulario.elements.prioridad.value = datos.prioridad;\n        resultadoIA.textContent =\n            "Sugerencia: " + datos.categoria + " / " + datos.prioridad +\n            "\\nMotivo: " + datos.justificacion +\n            "\\nRevisa estos valores antes de registrar.";\n    } catch (error) {\n        resultadoIA.textContent =\n            error.message + " Puedes completar el registro manualmente.";\n    } finally {\n        botonIA.disabled = false;\n    }\n});\n</script>\n\n</body>\n</html>\n'

@app.get("/")
def inicio():
    incidencias = list(tabla.query_entities(
        query_filter="PartitionKey eq @particion",
        parameters={"particion": PARTICION}
    ))
    for caso in incidencias:
        caso["id"] = caso["RowKey"]
    incidencias.sort(key=lambda caso: caso["creada_en"], reverse=True)
    return render_template_string(
        PAGINA, incidencias=incidencias, categorias=CATEGORIAS
    )


@app.post("/incidencias")
def registrar():
    ubicacion = request.form.get("ubicacion", "").strip()
    categoria = request.form.get("categoria", "")
    descripcion = request.form.get("descripcion", "").strip()
    prioridad = request.form.get("prioridad", "")

    if (
        not ubicacion or len(ubicacion) > 120
        or not descripcion or len(descripcion) > 2000
        or categoria not in CATEGORIAS
        or prioridad not in PRIORIDADES
    ):
        return "Datos invalidos. Regresa y revisa el formulario.", 400

    tabla.create_entity({
        "PartitionKey": PARTICION,
        "RowKey": uuid4().hex,
        "ubicacion": ubicacion,
        "categoria": categoria,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "estado": "Pendiente",
        "creada_en": datetime.now(timezone.utc).isoformat()
    })
    return redirect(url_for("inicio"))


@app.post("/incidencias/<incidencia_id>/avanzar")
def avanzar_estado(incidencia_id):
    if len(incidencia_id) != 32 or any(
        c not in "0123456789abcdef" for c in incidencia_id
    ):
        return "Incidencia no encontrada.", 404

    try:
        caso = tabla.get_entity(PARTICION, incidencia_id)
    except ResourceNotFoundError:
        return "Incidencia no encontrada.", 404

    if request.form.get("estado_actual") != caso["estado"]:
        return "El estado cambio. Regresa y actualiza la pagina.", 409

    transiciones = {
        "Pendiente": "En atenci\u00f3n",
        "En atenci\u00f3n": "Resuelto"
    }
    nuevo_estado = transiciones.get(caso["estado"])
    if nuevo_estado is None:
        return "La incidencia ya esta resuelta.", 409

    try:
        tabla.update_entity(
            entity={
                "PartitionKey": PARTICION,
                "RowKey": incidencia_id,
                "estado": nuevo_estado,
                "actualizada_en": datetime.now(timezone.utc).isoformat()
            },
            mode=UpdateMode.MERGE,
            etag=caso.metadata["etag"],
            match_condition=MatchConditions.IfNotModified
        )
    except HttpResponseError as error:
        if error.status_code == 412:
            return "Otro proceso modifico el caso. Actualiza la pagina.", 409
        raise

    return redirect(url_for("inicio"))


@app.errorhandler(HttpResponseError)
def error_azure(error):
    app.logger.exception("Fallo al acceder a Azure Tables")
    return "No se pudo acceder a Azure. Revisa el detalle en PowerShell.", 503



@app.post("/sugerir-ia")
def sugerir_ia():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify(error="Solicitud invalida."), 400

    ubicacion = datos.get("ubicacion")
    descripcion = datos.get("descripcion")
    if not isinstance(ubicacion, str) or not isinstance(descripcion, str):
        return jsonify(error="Completa ubicacion y descripcion."), 400

    ubicacion = ubicacion.strip()
    descripcion = descripcion.strip()
    if not (1 <= len(ubicacion) <= 120 and 1 <= len(descripcion) <= 2000):
        return jsonify(error="Revisa la longitud de los campos."), 400

    try:
        with AIProjectClient(
            endpoint=(
                "https://cryptohuerta-7931-resource.services.ai.azure.com"
                "/api/projects/cryptohuerta-7931"
            ),
            credential=credencial,
            allow_preview=True,
        ) as proyecto:
            with proyecto.get_openai_client(
                agent_name="sg360-asistente"
            ) as cliente:
                conversacion = cliente.conversations.create()
                respuesta = cliente.responses.create(
                    conversation=conversacion.id,
                    input=[{
                        "role": "user",
                        "content": json.dumps({
                            "ubicacion": ubicacion,
                            "descripcion": descripcion
                        }, ensure_ascii=False)
                    }],
                )

        texto = respuesta.output_text.strip()
        if texto.startswith("```") and texto.endswith("```"):
            texto = "\n".join(texto.splitlines()[1:-1]).strip()
        sugerencia = json.loads(texto)

        if not isinstance(sugerencia, dict):
            raise ValueError("La respuesta no es un objeto JSON.")

        categoria = sugerencia.get("categoria")
        prioridad = sugerencia.get("prioridad")
        motivo = sugerencia.get("justificacion")
        pregunta = sugerencia.get("pregunta_aclaratoria")

        if categoria is not None and categoria not in CATEGORIAS:
            raise ValueError("Categoria no permitida.")
        if prioridad is not None and prioridad not in PRIORIDADES:
            raise ValueError("Prioridad no permitida.")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("Falta justificacion.")
        if pregunta is not None and not isinstance(pregunta, str):
            raise ValueError("Pregunta invalida.")
        if (categoria is None or prioridad is None) and (
            not isinstance(pregunta, str) or not pregunta.strip()
        ):
            raise ValueError("Falta pregunta aclaratoria.")
        if sugerencia.get("requiere_revision_humana") is not True:
            raise ValueError("Falta revision humana.")

        return jsonify(
            categoria=categoria,
            prioridad=prioridad,
            justificacion=motivo,
            pregunta_aclaratoria=pregunta,
            requiere_revision_humana=True
        )

    except (AzureError, APIError, ValueError, TypeError, AttributeError):
        app.logger.exception("Fallo al consultar el asistente de Foundry")
        return jsonify(
            error="La IA no pudo generar una sugerencia valida."
        ), 502


if __name__ == "__main__":
    print("Verificando acceso a Azure...")
    next(iter(tabla.list_entities(results_per_page=1)), None)
    print("Azure conectado. Abre http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
