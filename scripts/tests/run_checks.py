#!/usr/bin/env python3
"""Corre los checks de `scripts/tests` por area, no siempre los 30.

No hay runner ni CI en este repo: hasta ahora se corria un `for` a mano sobre todos los
`check_*`, y un cambio de plantillas pagaba los checks de migraciones o de carga de Excel.

Uso:
    python scripts/tests/run_checks.py --list
    python scripts/tests/run_checks.py                      # todo (como antes)
    python scripts/tests/run_checks.py --scope templates    # agregar/cambiar plantillas
    python scripts/tests/run_checks.py --scope templates,masivo
    python scripts/tests/run_checks.py --scope llamadas --solo-fallas

Reglas:
  * Cada check pertenece a UN area. Si aparece un `check_*.py`/`check_*.js` nuevo y no
    esta clasificado, el runner aborta: asi nadie queda sin correr por olvido.
  * Corre secuencial y desde la raiz del repo, igual que a mano (los checks leen
    `frontend/call_center.js` y `backend/main.py` con rutas relativas).
  * Salida: `0` si todo paso, `1` si algo fallo o si el mapa esta incompleto.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]

# --- Mapa check -> area -------------------------------------------------------------
# `templates`: catalogo de WhatsApp (cuerpos, params, 1x1, masivo, previews, visibilidad,
#              campo dia, refresco del catalogo). Es el area que se toca al agregar,
#              renombrar o corregir una plantilla.
# `masivo`: UI del envio multiple que no lee el catalogo (filtro de estados del link masivo).
# `llamadas`: migraciones, mapeo de columnas del Excel y carga de llamadas.
SCOPES: dict[str, list[str]] = {
    "templates": [
        "check_729_sin_bono.py",
        "check_853_sin_bono.py",
        "check_el_azul.py",
        "check_entrega_sibate_oct19_templates.py",
        "check_fatiga_729_r3.py",
        "check_final_beta.py",
        "check_noviembre_9_sibate_templates.py",
        "check_plantillas_250_noviembre.py",
        "check_primera_recogida_853.py",
        "check_recibido_hoy.py",
        "check_recordatorio_sibate_204_302.py",
        "check_serum_1_llamada.py",
        "check_shampo_729.py",
        "check_shampo_primer_853.py",
        "check_sibate_encuesta_final.py",
        "check_single_templates.py",
        "check_single_templates_regression.py",
        "check_template_visibility.py",
        "check_template_visibility_edges.py",
        "check_853_sin_bono_preview.js",
        "check_el_azul_preview.js",
        "check_fatiga_729_r3_preview.js",
        "check_final_beta_preview.js",
        "check_noviembre_9_sibate_preview.js",
        "check_plantillas_250_noviembre_preview.js",
        "check_primera_recogida_853_preview.js",
        "check_recordatorio_sibate_preview.js",
        "check_shampo_729_preview.js",
        "check_template_catalog_refresh.js",
        "check_template_day_preview.js",
        # Valida que el select compartido 1x1/masivo quede con una key valida del catalogo:
        # si una plantilla se renombra o se saca, este check lo detecta.
        "check_new_chat_bulk_default.js",
    ],
    "masivo": [
        "check_bulk_status_filter.js",
    ],
    "llamadas": [
        "check_calls_migration.py",
        "check_column_mapping.py",
        "check_upload_calls.py",
    ],
}


def checks_en_disco() -> list[str]:
    return sorted(
        p.name
        for p in DIR.iterdir()
        if p.is_file() and p.name.startswith("check_") and p.suffix in (".py", ".js")
    )


def clasificar() -> dict[str, str]:
    mapa: dict[str, str] = {}
    for scope, nombres in SCOPES.items():
        for nombre in nombres:
            if nombre in mapa:
                raise SystemExit(
                    f"mapa roto: {nombre} esta en '{mapa[nombre]}' y en '{scope}'"
                )
            mapa[nombre] = scope
    return mapa


def validar_cobertura(mapa: dict[str, str]) -> list[str]:
    en_disco = set(checks_en_disco())
    sin_clasificar = sorted(en_disco - set(mapa))
    inexistentes = sorted(set(mapa) - en_disco)
    if sin_clasificar:
        raise SystemExit(
            "checks sin clasificar en SCOPES (agregalos al area que corresponda):\n  "
            + "\n  ".join(sin_clasificar)
        )
    if inexistentes:
        raise SystemExit(
            "SCOPES nombra checks que no existen en el directorio:\n  "
            + "\n  ".join(inexistentes)
        )
    return sorted(en_disco)


def seleccionar(scopes: list[str], mapa: dict[str, str], todos: list[str]) -> list[str]:
    if "todo" in scopes:
        return todos
    elegidos = [n for n in todos if mapa[n] in scopes]
    if not elegidos:
        raise SystemExit(f"scope sin checks: {', '.join(scopes)}")
    return elegidos


def comando(nombre: str) -> list[str]:
    ruta = str(DIR / nombre)
    if nombre.endswith(".py"):
        return [sys.executable, ruta]
    return ["node", ruta]


def lineas_de_falla(salida: str) -> list[str]:
    interesantes = [
        ln
        for ln in salida.splitlines()
        if "FALLA" in ln or "Traceback" in ln or "Error" in ln or "error" in ln
    ]
    if not interesantes:
        interesantes = salida.splitlines()[-15:]
    return interesantes[:25]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Corre los checks de scripts/tests por area.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scope",
        default="todo",
        help="todo | %s (acepta varios separados por coma)"
        % " | ".join(SCOPES),
    )
    parser.add_argument(
        "--list", action="store_true", help="muestra el mapa check -> area y sale"
    )
    parser.add_argument(
        "--timeout", type=int, default=300, help="segundos maximos por check (300)"
    )
    parser.add_argument(
        "--solo-fallas",
        action="store_true",
        help="no imprime la linea de los checks que pasan",
    )
    args = parser.parse_args()

    mapa = clasificar()
    todos = validar_cobertura(mapa)

    if args.list:
        print(f"{len(todos)} checks en {DIR}:\n")
        for scope, nombres in SCOPES.items():
            print(f"  {scope} ({len(nombres)})")
            for nombre in nombres:
                print(f"    {nombre}")
        print("\n  todo = " + " + ".join(f"{s} ({len(n)})" for s, n in SCOPES.items()))
        return 0

    scopes = [s.strip() for s in args.scope.split(",") if s.strip()]
    desconocidos = [s for s in scopes if s != "todo" and s not in SCOPES]
    if desconocidos:
        raise SystemExit(
            "scope desconocido: %s (validos: todo, %s)"
            % (", ".join(desconocidos), ", ".join(SCOPES))
        )

    elegidos = seleccionar(scopes, mapa, todos)
    print(
        "Corriendo %d checks (scope=%s) desde %s\n" % (len(elegidos), args.scope, RAIZ)
    )

    fallas: list[str] = []
    inicio = time.time()
    for i, nombre in enumerate(elegidos, 1):
        etiqueta = "[%d/%d] %-46s" % (i, len(elegidos), nombre)
        arranque = time.time()
        try:
            proc = subprocess.run(
                comando(nombre),
                cwd=str(RAIZ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=args.timeout,
            )
            codigo, salida = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
            motivo = "fallo"
        except subprocess.TimeoutExpired as exc:
            codigo = 124
            salida = (exc.stdout or "") + (exc.stderr or "")
            motivo = f"timeout {args.timeout}s"
        except FileNotFoundError:
            codigo = 127
            salida = ""
            motivo = "no se pudo ejecutar (falta node o python)"

        segundos = time.time() - arranque
        if codigo == 0:
            if not args.solo_fallas:
                print(f"{etiqueta} OK   ({segundos:.1f} s)")
        else:
            fallas.append(nombre)
            print(f"{etiqueta} FALLA ({segundos:.1f} s, {motivo}, exit {codigo})")
            for ln in lineas_de_falla(salida):
                print("      " + ln)

    total = time.time() - inicio
    print(
        "\nRESUMEN scope=%s: %d OK, %d FALLA en %.1f s"
        % (args.scope, len(elegidos) - len(fallas), len(fallas), total)
    )
    if fallas:
        print("Fallaron:\n  " + "\n  ".join(fallas))
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
