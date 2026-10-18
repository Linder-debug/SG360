from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "incidencias.db"


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


with conectar() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS incidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ubicacion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            creada_en TEXT NOT NULL
        )
    """)


PAGINA = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SG360 · Incidencias</title>
    <style>
        body {font-family: Arial; background: #f3f6fa; color: #183047;
              max-width: 1100px; margin: 40px auto; padding: 0 20px}
        .panel {background: white; padding: 24px; border-radius: 12px;
                margin-bottom: 24px}
        label {display: block; margin-top: 14px}
        input, select, textarea {box-sizing: border-box; width: 100%;
               padding: 10px; margin-top: 6px; border: 1px solid #bbc7d4;
               border-radius: 6px}
        button {background: #0067b8; color: white; border: 0;
                padding: 12px 20px; border-radius: 6px; margin-top: 18px;
                cursor: pointer}
        table {width: 100%; border-collapse: collapse}
        th, td {text-align: left; padding: 12px; border-bottom: 1px solid #ddd}
        td {overflow-wrap: anywhere}
        .tabla {overflow-x: auto}
    </style>
</head>
<body>
    <h1>SG360</h1>
    <p>Gestión de incidencias de servicios generales · Prototipo académico</p>
    <section class="panel">
        <h2>Registrar incidencia</h2>
        <form method="post" action="{{ url_for('registrar') }}">
            <label>Ubicación
                <input name="ubicacion" maxlength="120" required
                       placeholder="Ejemplo: Comedor principal">
            </label>
            <label>Categoría
                <select name="categoria">
                    {% for categoria in categorias %}
                    <option>{{ categoria }}</option>
                    {% endfor %}
                </select>
            </label>
            <label>Descripción
                <textarea name="descripcion" maxlength="2000"
                          rows="3" required></textarea>
            </label>
            <label>Prioridad
                <select name="prioridad">
                    <option>Baja</option>
                    <option selected>Media</option>
                    <option>Alta</option>
                </select>
            </label>
            <button type="submit">Registrar incidencia</button>
        </form>
    </section>
    <section class="panel">
        <h2>Incidencias registradas: {{ incidencias | length }}</h2>
        <div class="tabla">
        <table>
            <thead>
                <tr>
                    <th>Código</th><th>Ubicación</th><th>Categoría</th>
                    <th>Descripción</th><th>Prioridad</th><th>Estado</th><th>Acción</th>
                </tr>
            </thead>
            <tbody>
                {% for caso in incidencias %}
                <tr>
                    <td>SG-{{ "%04d" | format(caso.id) }}</td>
                    <td>{{ caso.ubicacion }}</td>
                    <td>{{ caso.categoria }}</td>
                    <td>{{ caso.descripcion }}</td>
                    <td>{{ caso.prioridad }}</td>
                    <td>{{ caso.estado }}</td>
                    <td>
                        {% if caso.estado != 'Resuelto' %}
                         <form method="post"
                        action="{{ url_for('avanzar_estado', incidencia_id=caso.id) }}">
                        <button type="submit">
                        {% if caso.estado == 'Pendiente' %}
                             Iniciar atención
                         {% else %}
                            Marcar resuelto
                        {% endif %}
                        </button>
                        </form>
                        {% else %}
                            Atención finalizada
                            {% endif %}
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="7">Todavía no hay incidencias.</td></tr>
                {% endfor %}
            </tbody>
        </table>
        </div>
    </section>
</body>
</html>
"""

CATEGORIAS = ("Mantenimiento", "Limpieza", "Transporte", "Otros")
PRIORIDADES = ("Baja", "Media", "Alta")


@app.get("/")
def inicio():
    with conectar() as db:
        incidencias = db.execute(
            "SELECT * FROM incidencias ORDER BY id DESC"
        ).fetchall()
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
        return "Datos inválidos. Regresa y revisa el formulario.", 400

    with conectar() as db:
        db.execute("""
            INSERT INTO incidencias
            (ubicacion, categoria, descripcion, prioridad, creada_en)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ubicacion, categoria, descripcion, prioridad,
            datetime.now(timezone.utc).isoformat()
        ))
    return redirect(url_for("inicio"))


@app.post("/incidencias/<int:incidencia_id>/avanzar")
def avanzar_estado(incidencia_id):
    transiciones = {
        "Pendiente": "En atención",
        "En atención": "Resuelto",
    }

    with conectar() as db:
        caso = db.execute(
            "SELECT estado FROM incidencias WHERE id = ?",
            (incidencia_id,)
        ).fetchone()

        if caso is None:
            return "Incidencia no encontrada.", 404

        nuevo_estado = transiciones.get(caso["estado"])

        if nuevo_estado is None:
            return "La incidencia ya está resuelta.", 409

        db.execute(
            "UPDATE incidencias SET estado = ? WHERE id = ? AND estado = ?",
            (nuevo_estado, incidencia_id, caso["estado"])
        )

    return redirect(url_for("inicio"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)