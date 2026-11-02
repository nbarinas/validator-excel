#!/usr/bin/env python3
"""Verifica la plantilla `recibido` con la fecha relativa ("a partir de hoy").

Pedido del usuario (verbatim): *"recibido · Spanish ... que comenzarás a utilizar
a partir de hoy ... para que me ayudes a 1x1, masivo y previsualizacion"*.

Reemplaza el cuerpo con fecha fija ("miércoles 28 de octubre") por "a partir de
hoy", y habilita la plantilla para el envío 1x1 (hasta ahora sólo estaba en el
masivo).

Comprueba contra el codigo real:
  1. WHATSAPP_TEMPLATE_BODIES['recibido'] es byte-exacto al texto aprobado
     (sin punto final tras "hoy", tal como llega de Meta, y con las comillas
     tipograficas de “RECIBIDO”).
  2. El catalogo (/whatsapp/templates) publica ese cuerpo, con single_eligible=True
     (1x1) y presente en el catalogo completo del masivo.
  3. El render del texto libre sustituye {{encuestada}} y no toca “RECIBIDO”.
  4. frontend/call_center.js guarda el mismo literal en BULK_TEMPLATE_BODIES
     (respaldo de la vista previa del masivo).

Uso:    python scripts/tests/check_recibido_hoy.py
Salida: 0 = todo OK; 1 = hay diferencias.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import backend.main as main  # noqa: E402

KEY = "recibido"

# --- Cuerpo esperado (verbatim del pedido: sin punto final tras "hoy") ---
CUERPO = (
    "Hola, {{encuestada}} 😊\n"
    "\n"
    "Te saluda el equipo de AZ Marketing Plus.\n"
    "\n"
    "Te escribimos para confirmar que el transportador ya te hizo entrega del "
    "producto, que comenzarás a utilizar a partir de hoy\n"
    "\n"
    "Por favor, respóndenos “RECIBIDO” para confirmar que ya lo tienes.\n"
    "\n"
    "¡Muchas gracias! 🙌"
)

# Fechas fijas de versiones anteriores: ya no deben aparecer.
VIEJO_28 = "28 de octubre"
VIEJO_5 = "5 de octubre"

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
    check(VIEJO_28 not in (real or ""), f"{KEY} ya no menciona '{VIEJO_28}'")
    check(VIEJO_5 not in (real or ""), f"{KEY} ya no menciona '{VIEJO_5}'")
    check("a partir de hoy" in (real or ""), f"{KEY} dice 'a partir de hoy'")
    check("“RECIBIDO”" in (real or ""), f"{KEY} conserva las comillas tipograficas de “RECIBIDO”")

    print("[2] El catalogo publica ese cuerpo en 1x1 y en el masivo")
    catalogo = main.whatsapp_templates_catalog(db=None, current_user=_SuperUser())
    item = next((t for t in catalogo if t["key"] == KEY), None)
    check(item is not None, f"{KEY} esta en /whatsapp/templates")
    if item:
        check(item["body"] == CUERPO, f"{KEY} body del catalogo byte-exacto")
        check(item["name"] == "recibido", f"{KEY} name del payload a Meta: {item['name']}")
        check(item["language"] == "es", f"{KEY} language: {item['language']}")
        check(item["params"] == ["encuestada"], f"{KEY} params: {item['params']}")
        check(item["label"] == "Confirmar recepción del producto", f"{KEY} label: {item['label']}")
        check(item["single_eligible"] is True, f"{KEY} habilitada para 1x1 (single_eligible)")
    check(KEY in main.WHATSAPP_SINGLE_TEMPLATE_KEYS,
          f"{KEY} esta en WHATSAPP_SINGLE_TEMPLATE_KEYS (boton Plantillas 1x1)")
    claves_masivo = [t["key"] for t in catalogo]
    check(set(claves_masivo) == set(main.WHATSAPP_TEMPLATE_MAP),
          "el masivo conserva todo el catalogo")
    check(KEY in claves_masivo, f"{KEY} aparece en el catalogo del masivo")

    print("[3] El render del texto libre sustituye la variable")
    render = main._wa_render_template_body(KEY, {"encuestada": "María"})
    check(render is not None, f"{KEY} se puede renderizar como texto libre")
    check("{{" not in (render or ""), f"{KEY} render sin variables pendientes")
    check("Hola, María 😊" in (render or ""), f"{KEY} render sustituye encuestada")
    check("“RECIBIDO”" in (render or ""), f"{KEY} render conserva “RECIBIDO”")

    print("[4] El front guarda el mismo literal (vista previa del masivo)")
    js = (RAIZ / "frontend" / "call_center.js").read_text(encoding="utf-8")
    match = re.search(r"^\s*'%s':\s*'((?:[^'\\]|\\.)*)'\s*," % KEY, js, re.MULTILINE)
    front_body = json.loads('"%s"' % match.group(1)) if match else None
    check(front_body is not None, f"BULK_TEMPLATE_BODIES define {KEY} en el front")
    check(front_body == CUERPO, f"{KEY} del front coincide byte-exacto con el backend")
    check(VIEJO_28 not in (front_body or ""), f"{KEY} del front ya no menciona '{VIEJO_28}'")


if __name__ == "__main__":
    correr()
    if FALLAS:
        print(f"\n{len(FALLAS)} fallas.")
        sys.exit(1)
    print("\nTodo OK.")
