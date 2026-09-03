#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime, timezone

import requests


API_URL = "https://api.github.com/users/{}"

HEADERS = {
    "User-Agent": "GxBotHunter/1.0"
}

TIMEOUT = 10
RESULTS_DIR = "reports"


def obtener_perfil(username):
    url = API_URL.format(username)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

    except requests.RequestException as error:
        print(f"[!] Error de conexión: {error}")
        return None

    if response.status_code == 404:
        print("[!] Usuario no encontrado.")
        return None

    if response.status_code != 200:
        print(
            f"[!] GitHub respondió "
            f"con HTTP {response.status_code}"
        )
        return None

    try:
        return response.json()

    except ValueError:
        print("[!] Respuesta JSON inválida.")
        return None


def calcular_riesgo(profile):
    score = 0
    indicadores = []

    repos = profile.get("public_repos", 0)
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)

    if repos >= 100:
        score += 20
        indicadores.append(
            "Cantidad elevada de repositorios públicos"
        )

    if followers == 0 and following >= 100:
        score += 20
        indicadores.append(
            "Muchos usuarios seguidos y ningún seguidor"
        )

    if following >= 500:
        score += 15
        indicadores.append(
            "Cantidad elevada de cuentas seguidas"
        )

    if followers >= 100:
        score -= 10
        indicadores.append(
            "Cuenta con una cantidad considerable de seguidores"
        )

    if profile.get("bio"):
        score -= 5

    if profile.get("name"):
        score -= 5

    score = max(0, min(score, 100))

    if score < 30:
        nivel = "BAJO"

    elif score < 60:
        nivel = "MEDIO"

    else:
        nivel = "ALTO"

    return score, nivel, indicadores


def guardar_reporte(profile, score, nivel, indicadores):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    username = profile.get("login", "unknown")

    reporte = {
        "tool": "GxBotHunter",
        "fecha": datetime.now(
            timezone.utc
        ).isoformat(),
        "usuario": username,
        "perfil": {
            "nombre": profile.get("name"),
            "bio": profile.get("bio"),
            "repositorios": profile.get("public_repos"),
            "seguidores": profile.get("followers"),
            "siguiendo": profile.get("following"),
            "creado": profile.get("created_at"),
        },
        "analisis": {
            "riesgo_estimado": score,
            "nivel": nivel,
            "indicadores": indicadores
        }
    }

    path = os.path.join(
        RESULTS_DIR,
        f"{username}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            reporte,
            file,
            indent=4,
            ensure_ascii=False
        )

    return path


def main():
    print("=" * 60)
    print("                 GxBotHunter")
    print("       Análisis heurístico de perfiles públicos")
    print("=" * 60)

    username = (
        sys.argv[1]
        if len(sys.argv) > 1
        else input("Usuario de GitHub: ").strip()
    )

    if not username:
        print("[!] Debes proporcionar un usuario.")
        return

    print()
    print(f"[+] Analizando: {username}")

    profile = obtener_perfil(username)

    if profile is None:
        return

    score, nivel, indicadores = calcular_riesgo(
        profile
    )

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)

    print(f"Usuario       : {profile.get('login')}")
    print(f"Nombre        : {profile.get('name')}")
    print(
        f"Repositorios  : "
        f"{profile.get('public_repos')}"
    )
    print(
        f"Seguidores    : "
        f"{profile.get('followers')}"
    )
    print(
        f"Siguiendo     : "
        f"{profile.get('following')}"
    )

    print()
    print(
        f"Riesgo estimado : {score}%"
    )
    print(
        f"Nivel           : {nivel}"
    )

    print()
    print("Indicadores:")

    if indicadores:
        for item in indicadores:
            print(f"- {item}")
    else:
        print("- No se encontraron indicadores.")

    report = guardar_reporte(
        profile,
        score,
        nivel,
        indicadores
    )

    print()
    print(f"[+] Reporte: {report}")
    print(
        "[!] El porcentaje es una heurística y "
        "no confirma que el usuario sea un bot."
    )


if __name__ == "__main__":
    main()