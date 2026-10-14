"""
Cliente de consola para la API de Gestión de Tareas (PFO 2).
Permite registrarse, iniciar sesión y ver la página de bienvenida (/tareas).
Requiere: pip install requests
"""

import requests

BASE_URL = "http://127.0.0.1:5000"

# La Session conserva la cookie que devuelve /login, así /tareas reconoce al usuario.
sesion = requests.Session()


def pedir_credenciales():
    usuario = input("Usuario: ").strip()
    contrasena = input("Contraseña: ")
    return {"usuario": usuario, "contraseña": contrasena}


def registrar():
    respuesta = sesion.post(f"{BASE_URL}/registro", json=pedir_credenciales())
    print(f"[{respuesta.status_code}] {respuesta.json()}")


def iniciar_sesion():
    respuesta = sesion.post(f"{BASE_URL}/login", json=pedir_credenciales())
    print(f"[{respuesta.status_code}] {respuesta.json()}")


def ver_tareas():
    respuesta = sesion.get(f"{BASE_URL}/tareas")
    print(f"[{respuesta.status_code}]")
    print(respuesta.text)


def main():
    opciones = {"1": registrar, "2": iniciar_sesion, "3": ver_tareas}

    while True:
        print("\n--- Gestión de Tareas ---")
        print("1. Registrarse")
        print("2. Iniciar sesión")
        print("3. Ver tareas")
        print("4. Salir")
        eleccion = input("Opción: ").strip()

        if eleccion == "4":
            print("Hasta luego.")
            break

        accion = opciones.get(eleccion)
        if accion is None:
            print("Opción inválida.")
            continue

        try:
            accion()
        except requests.exceptions.ConnectionError:
            print("[ERROR] No se pudo conectar al servidor. ¿Está corriendo servidor.py?")


if __name__ == "__main__":
    main()
