"""
PFO 2 - Sistema de Gestión de Tareas con API y Base de Datos
-------------------------------------------------------------
API REST con Flask + SQLite.

Endpoints:
    POST /registro  -> registra un usuario (contraseña hasheada)
    POST /login     -> verifica credenciales e inicia sesión
    GET  /tareas    -> HTML de bienvenida (requiere haber iniciado sesión)
"""

import os
import sqlite3
from html import escape

from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Clave usada para firmar la cookie de sesión. En producción se define por
# variable de entorno; el valor por defecto es solo para desarrollo/TP.
app.secret_key = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar")

DB_NAME = os.environ.get("DB_NAME", "tareas.db")


# =========================================================
# Base de datos
# =========================================================
def get_connection():
    """Abre una conexión a SQLite. Las filas se acceden por nombre de columna."""
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_db():
    """Crea la tabla 'usuarios' si no existe."""
    with get_connection() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )


def leer_credenciales():
    """
    Extrae usuario y contraseña del JSON del request.
    Devuelve (usuario, contraseña) o (None, None) si el cuerpo es inválido.
    """
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return None, None

    usuario = datos.get("usuario")
    contrasena = datos.get("contraseña")

    if not isinstance(usuario, str) or not isinstance(contrasena, str):
        return None, None

    usuario = usuario.strip()
    if not usuario or not contrasena:
        return None, None

    return usuario, contrasena


# =========================================================
# Endpoints
# =========================================================
@app.route("/registro", methods=["POST"])
def registro():
    """Registra un usuario nuevo guardando solo el hash de la contraseña."""
    usuario, contrasena = leer_credenciales()
    if usuario is None:
        return jsonify(
            {"error": 'Se espera JSON: {"usuario": "...", "contraseña": "..."}'}
        ), 400

    # generate_password_hash aplica un salt aleatorio y un algoritmo lento
    # (scrypt por defecto), por lo que nunca se almacena la contraseña real.
    password_hash = generate_password_hash(contrasena)

    try:
        with get_connection() as conexion:
            conexion.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario, password_hash),
            )
    except sqlite3.IntegrityError:
        # La columna 'usuario' es UNIQUE: ya existe ese nombre.
        return jsonify({"error": "El usuario ya existe"}), 409
    except sqlite3.Error as error:
        app.logger.error("Error de base de datos en /registro: %s", error)
        return jsonify({"error": "Error interno de base de datos"}), 500

    return jsonify({"mensaje": f"Usuario '{usuario}' registrado correctamente"}), 201


@app.route("/login", methods=["POST"])
def login():
    """Verifica las credenciales y, si son correctas, abre una sesión."""
    usuario, contrasena = leer_credenciales()
    if usuario is None:
        return jsonify(
            {"error": 'Se espera JSON: {"usuario": "...", "contraseña": "..."}'}
        ), 400

    try:
        with get_connection() as conexion:
            fila = conexion.execute(
                "SELECT password_hash FROM usuarios WHERE usuario = ?",
                (usuario,),
            ).fetchone()
    except sqlite3.Error as error:
        app.logger.error("Error de base de datos en /login: %s", error)
        return jsonify({"error": "Error interno de base de datos"}), 500

    # Mismo mensaje si el usuario no existe o la contraseña es incorrecta,
    # para no revelar qué usuarios están registrados.
    if fila is None or not check_password_hash(fila["password_hash"], contrasena):
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    session["usuario"] = usuario
    return jsonify({"mensaje": f"Bienvenido, {usuario}. Ya podés acceder a /tareas"}), 200


@app.route("/tareas", methods=["GET"])
def tareas():
    """Muestra el HTML de bienvenida. Solo accesible con sesión iniciada."""
    usuario = session.get("usuario")
    if usuario is None:
        return jsonify({"error": "No autorizado. Iniciá sesión en POST /login"}), 401

    # escape() evita inyectar HTML a través del nombre de usuario (XSS).
    nombre = escape(usuario)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Tareas</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #f4f6f8;
                display: flex; justify-content: center; align-items: center;
                min-height: 100vh; margin: 0; }}
        .tarjeta {{ background: #fff; padding: 2.5rem 3rem; border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,.08); text-align: center; }}
        h1 {{ margin: 0 0 .5rem; color: #1f2d3d; }}
        p  {{ margin: 0; color: #5b6b7b; }}
    </style>
</head>
<body>
    <div class="tarjeta">
        <h1>¡Bienvenido, {nombre}!</h1>
        <p>Sistema de Gestión de Tareas</p>
    </div>
</body>
</html>"""


# =========================================================
# Punto de entrada
# =========================================================
inicializar_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
