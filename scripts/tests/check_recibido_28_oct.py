#!/usr/bin/env python3
"""Verifica el cuerpo actualizado de la plantilla `recibido` (entrega 28 de octubre).

Pedido del usuario (verbatim): el cuerpo aprobado en Meta ahora dice
"... que comenzarás a utilizar a partir del miércoles 28 de octubre." y las
comillas de RECIBIDO son tipograficas ("RECIBIDO" con “ ”), no rectas.

Comprueba contra el codigo real:
  1. WHATSAPP_TEMPLATE_BODIES['recibido'] es byte-exacto al texto aprobado.
  2. El catalogo (/whatsapp/templates) publica ese mismo cuerpo.
  3. El render del texto libre sustituye {{encuestada}} y no deja variables.
  4. frontend/call_center.js guarda el mismo literal como respaldo de la vista
     previa (paridad backend/front, sin el texto viejo del 5 de octubre).

Uso:    python scripts/tests/check_recibido_28_oct.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import backend.main as main  # noqa: E402

KEY = "recibido"

# --- Cuerpo esperado (verbatim del pedido) ---
CUERPO = (
    "Hola, {{encuestada}} 😊\n"
    "\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Te escribimos para confirmar que el transportador ya te hizo entrega del "
    "producto, que comenzarás a utilizar a partir del miércoles 28 de octubre.\n"
    "\n"
    "Por favor, respóndenos “RECIBIDO” para confirmar que ya lo tienes.\n"
    "\n"
    "¡Muchas gracias! 🙌"
)

VIEJO = "lunes 5 de octubre"

FALLAS = []


def check(cond, msg):
    if cond:
        print(f"  OK    {msg}")
    else:
        print(f"  FALLA {msg}")
        FALLAS.append(msg)


class _SuperUser:
    role = "superuser"


def correr():
    print("[1] El cuerpo del backend es el aprobado en Meta")
    real = main.WHATSAPP_TEMPLATE_BODIES.get(KEY)
    check(real == CUERPO, f"{KEY} byte-exacto en WHATSAPP_TEMPLATE_BODIES")
    check(VIEJO not in (real or ""), f"{KEY} ya no menciona '{VIEJO}'")
    check("miércoles 28 de octubre" in (real or ""), f"{KEY} menciona el miércoles 28 de octubre")

    print("[2] El catalogo publica ese mismo cuerpo")
    catalogo = main.whatsapp_templates_catalog(db=None, current_user=_SuperUser())
    item = next((t for t in catalogo if t["key"] == KEY), None)
    check(item is not None, f"{KEY} esta en /whatsapp/templates")
    if item:
        check(item["body"] == CUERPO, f"{KEY} body del catalogo byte-exacto")
        check(item["name"] == "recibido", f"{KEY} name del payload a Meta: {item['name']}")
        check(item["language"] == "es", f"{KEY} language: {item['language']}")
        check(item["params"] == ["encuestada"], f"{KEY} params: {item['params']}")

    print("[3] El render del texto libre sustituye las variables")
    render = main._wa_render_template_body(KEY, {"encuestada": "Maria"})
    check(render is not None, f"{KEY} se puede renderizar como texto libre")
    check("{{" not in (render or ""), f"{KEY} render sin variables pendientes")
    check("Hola, Maria 😊" in (render or ""), f"{KEY} render sustituye encuestada")

    print("[4] El front guarda el mismo literal (respaldo de la vista previa)")
    js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    literal = "'%s': '%s'," % (KEY, CUERPO.replace("\n", "\\n"))
    check(literal in js, f"BULK_TEMPLATE_BODIES tiene el cuerpo de {KEY} (byte-exacto)")
    check(VIEJO not in js, f"frontend/call_center.js ya no menciona '{VIEJO}'")


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
